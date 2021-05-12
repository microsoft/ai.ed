import * as vscode from "vscode";
import { promisify } from "util";
import { exec, spawn } from "child_process";

import axios from "axios";
import * as https from "https";

import { requestTimeOut, shellCmdTimeOut } from "./constants";
import * as t from "./types";
import * as fs from "fs";
import * as c from "./constants";

export class Document implements t.DocumentStore {
  private _filePath: string;
  private _fixes: t.Fix;

  constructor(filePath: string, fixes: t.Fix) {
    this._filePath = filePath;
    this._fixes = fixes;
  }

  public get fixes() {
    return this._fixes;
  }
  public set fixes(value: t.Fix) {
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
  private storage: Map<string, t.DocumentStore>;

  constructor() {
    this.storage = new Map();
  }

  public getValue(key: string): t.DocumentStore | undefined {
    return this.storage.get(key);
  }

  public set(key: string, value: t.DocumentStore) {
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

export async function getFix(baseURL: string, data: t.Payload): Promise<t.Fix> {
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
    return response.data.repairs as t.Fix;
  } catch (error) {
    console.error(error);

    return undefined;
  }
}

// function runCommand(saveFilePath) {
//     // obtain newFileAbsolutePath / oldFileAbsolutePath

//     var oldDocText = fs.readFileSync(oldFileAbsolutePath);
//     fs.writeFileSync(newFileAbsolutePath, oldDocText);

//     const finalUri = vscode.Uri.file(newFileAbsolutePath);
//     vscode.workspace.openTextDocument(finalUri).then((doc) => {
//         vscode.window.showTextDocument(doc, {preview: false});
//     });
// }
