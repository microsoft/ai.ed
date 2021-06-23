/* To better understand/ appreciate the various interfaces declared here,
 * please refer MACER paper at https://arxiv.org/abs/2005.14015
*/

import * as vscode from "vscode";
import { promisify } from "util";
import { exec } from "child_process";
import axios from "axios";
import * as https from "https";

// request to backend server
export interface Payload {
  source: string;
  lastEditLine: number;
}

export interface Edit {
  type: string;           // type of edit operation - insert/ delete/ replace
  start: number;          // starting position of the edit to be made
  end: number;            // ending position of the edit to be made
  insertString: string;   // text to be inserted in the range defined above
}

export interface Feedback {
  fullText: string;       // complete Feedback Text 
  // partial Feedback Texts
  msg1: string;           // generic message quoting existance of error
  msg2: string;           // specific message quoting kind of edits required to correct
  misc: string;
  // relates to the type of edit - insert/ delete/ replace
  actionMsg: string;    
  action: string;       
  tokens: string[];       // actual tokens on which the above action has to be performed
  tokensText: string[];   // textual description of the above tokens
}

// response from backend server
export interface Response {
  lineNo: number;
  repairLine: string;     // corrected version of the erroneous source line
  editDiffs: Edit[];
  feedback: Feedback[];
  // representation the repair involved in making a fix.
  repairClasses: string[];
}

export type Fixes = Response[] | undefined;

export interface DocumentStore {
  filePath: string;
  fixes: Fixes;
}

export class Document implements DocumentStore {
  private _filePath: string;
  private _fixes: Fixes;

  constructor(filePath: string, fixes: Fixes) {
    this._filePath = filePath;
    this._fixes = fixes;
  }

  public get fixes() {
    return this._fixes;
  }
  public set fixes(value: Fixes) {
    this._fixes = value;
  }

  public get filePath() {
    return this._filePath;
  }
  public set filePath(value: string) {
    this._filePath = value;
  }
}

export const serverURL: string | undefined = vscode.workspace
  .getConfiguration("python-hints")
  .get("webServerPath");

export const requestTimeOut: number = 100000;
export const shellCmdTimeOut: number = 10000;

export async function compileAndGetFix(
  document: vscode.TextDocument,
  documentStore: Map<string, DocumentStore>
): Promise<Fixes> {
  const filePath = document.uri.fsPath;
  let fixes: Fixes = undefined;
  let docHistory = documentStore.get(filePath);

  // TODO: What if the document was left in an inconsistent state previously
  // Can handle this case in the document open/ close event?

  // compile if file has either not been examined previously (in the history of the extension) ||
  // it has been modified
  let shouldCompile = docHistory === undefined || document.isDirty;

  docHistory = docHistory ?? { filePath: filePath, fixes: fixes };

  if (shouldCompile) {
    fixes = await compileAndGetFixHelper();
    docHistory.fixes = fixes;
    documentStore.set(filePath, docHistory);
  } else {
    fixes = docHistory.fixes;
    if (fixes !== undefined) {
      console.log("Saved fixes from History:");
    }
  }

  return fixes;
}

async function compileAndGetFixHelper(): Promise<Fixes> {
  // TODO: What if user changes tab immediately? - activeEditor changes - cancellation token?
  //* Or find an alternate way to get fullText of document and simply pass document along
  const activeEditor = vscode.window.activeTextEditor;

  if (activeEditor !== undefined) {
    const document = activeEditor.document;
    const cursorPosition = activeEditor.selection.active;
    const filePath = document.uri.fsPath;
    let result: Fixes = undefined;

    console.log(`Compiling ${filePath}`);
    const compiled = await compile(filePath);

    if (!compiled) {
      console.log("Syntax Error -> Preparing and Sending data...");

      const data: Payload = {
        source: document.getText(),
        lastEditLine: cursorPosition.line,
      };
      const payload: Payload = JSON.parse(JSON.stringify(data));

      if (serverURL === undefined) {
        console.log("Web Server path invalid");
      } else {
        result = await getFix(serverURL!, payload);
        if (result !== undefined) {
          console.log("Reply from Server:");
        }
      }
    }

    return result;
  }
}

export async function compile(
  filePath: string
): Promise<boolean> {

  const command = `python -m py_compile "${filePath}"`;
  const options = {
    windowsHide: true,
    timeout: shellCmdTimeOut,
  };

  let status: boolean = true;
  try {
    const execute = promisify(exec);
    const { stdout, stderr } = await execute(command, options);
    if (stderr) {
      status = false;
    }
  } catch (exception) {
    status = false;
  }

  return status;

}

export async function getFix(
  serverURL: string, 
  data: Payload
): Promise<Fixes> {

  // Ignore SSL certificate validation in request
  const agent = new https.Agent({
    rejectUnauthorized: false,
  });

  let result: Fixes | undefined = undefined;
  try {
    const response = await axios.post(serverURL, data, {
      timeout: requestTimeOut,
      httpsAgent: agent,
    });
    result = response.data.repairs as Fixes;
  } catch (error) {
    console.error(error);
  }

  return result;

}
