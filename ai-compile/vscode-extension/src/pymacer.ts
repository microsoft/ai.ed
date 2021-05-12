import * as vscode from "vscode";
import { promisify } from "util";
import { exec, spawn } from "child_process";

import axios from "axios";
import * as https from "https";
import * as fs from "fs";


export interface Payload {
  source: string;
  lastEditLine: number;
}

export interface Edit {
  type: string;
  start: number;
  end: number;
  insertString: string;
}

export interface Feedback {
  fullText: string;
  msg1: string;
  msg2: string;
  misc: string;
  actionMsg: string;
  action: string;
  tokens: string[];
  tokensText: string[];
}

export interface Response {
  lineNo: number;
  repairLine: string;
  editDiffs: Edit[];
  feedback: Feedback[];
  repairClasses: string[];
}

export interface DocumentStore {
  // TODO: Can this be made private? Does it make sense?
  filePath: string;
  fixes: Fix;
}

export type Fix = Response[] | undefined;

export const baseURL: string | undefined = vscode.workspace
  .getConfiguration("python-hints")
  .get("webServerPath");

export const requestTimeOut: number = 100000;
export const shellCmdTimeOut: number = 10000;
export const DEBUG: boolean = true;

export async function compileAndGetFix(
  document: vscode.TextDocument,
  docStore: Map<string, DocumentStore>
): Promise<Fix> {
  const filePath = document.uri.fsPath;
  let fixes: Fix = undefined;
  let docHistory = docStore.get(filePath);

  // TODO: What if the document was left in an inconsistent state previously
  // * Can handle this case in the document open/ close event?
  // compile if file has either not been examined previously (in the history of the extension) ||
  // it has been modified
  let compileFlag = docHistory === undefined || document.isDirty;

  // docHistory = docHistory?? new Document( filePath, undefined );
  // docHistory = docHistory?? {filePath: filePath, fixes: fixes};
  docHistory = docHistory ?? { filePath: filePath, fixes: fixes };

  if (compileFlag) {
    fixes = await compileAndGetFixHelper();
    docHistory.fixes = fixes;
    docStore.set(filePath, docHistory);
  } else {
    fixes = docHistory.fixes;
    if (fixes !== undefined) {
      console.log("Saved fixes from History:");
    }
  }

  return fixes;
}

async function compileAndGetFixHelper(): Promise<Fix> {
  // TODO: What if user changes tab immediately? - activeEditor changes - cancellation token?
  //* Or find an alternate way to get fullText of document and simply pass document along
  const activeEditor = vscode.window.activeTextEditor;

  if (activeEditor !== undefined) {
    const document = activeEditor.document;
    const cursorPosition = activeEditor.selection.active;
    const filePath = document.uri.fsPath;
    let result: Fix = undefined;

    console.log(`Compiling ${filePath}`);
    const compiled = await compile(filePath);

    if (!compiled) {
      console.log("Syntax Error -> Preparing and Sending data...");

      const data: Payload = {
        // srcCode: getDocumentText( document ),
        source: document.getText(),
        lastEditLine: cursorPosition.line,
      };
      const payload: Payload = JSON.parse(JSON.stringify(data));

      if (baseURL === undefined) {
        console.log("Web Server path invalid");
        return undefined;
      } else {
        result = await getFix(baseURL!, payload);
        if (result !== undefined) {
          console.log("Reply from Server:");
        }
      }
    }

    return result;
  }
}

export class Document implements DocumentStore {
  private _filePath: string;
  private _fixes: Fix;

  constructor(filePath: string, fixes: Fix) {
    this._filePath = filePath;
    this._fixes = fixes;
  }

  public get fixes() {
    return this._fixes;
  }
  public set fixes(value: Fix) {
    this._fixes = value;
  }

  public get filePath() {
    return this._filePath;
  }
  public set filePath(value: string) {
    this._filePath = value;
  }
}

export class DocStore {
  private storage: Map<string, DocumentStore>;

  constructor() {
    this.storage = new Map();
  }

  public getValue(key: string): DocumentStore | undefined {
    return this.storage.get(key);
  }

  public set(key: string, value: DocumentStore) {
    this.storage.set(key, value);
  }

  /*
  public getValue<T>(key: string): T | undefined {
    return this.storage.get<T>(key);
  }
  public setValue<T>(key: string, value: T) {
    this.storage.update(key, value);
  }
*/
}

export async function compile(filePath: string): Promise<boolean> {
  // TODO: Enforce python/ py_compile module dependency?
  const command = `python -m py_compile "${filePath}"`;
  const options = {
    windowsHide: true,
    timeout: shellCmdTimeOut,
  };
  try {
    // const script = spawn ("python", args, options);
    /* // TODO: Differentiate between:
		! fail due to command (missing module etc.)
		! fail due to syntax error
		Both of which return exit code 1
		*/
    const execute = promisify(exec);
    const { stdout, stderr } = await execute(command, options);
    if (stderr) {
      // console.error(`error: ${stderr}`);
      return false;
    }
    // console.log(`output ${stdout}`);
    return true;
  } catch (exception) {
    // console.error(`error: ${exception}`);
    return false;
  }
}

export async function getFix(baseURL: string, data: Payload): Promise<Fix> {
  process.env.NODE_TLS_REJECT_UNAUTHORIZED = "0";
  const agent = new https.Agent({
    rejectUnauthorized: false,
  });
  try {
    const response = await axios.post(baseURL, data, {
      timeout: requestTimeOut,
      httpsAgent: agent,
    });
    // console.log("response", response.data.repairs);
    return response.data.repairs as Fix;
  } catch (error) {
    console.error(error);

    return undefined;
  }
}
