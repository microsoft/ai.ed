// The module 'vscode' contains the VS Code extensibility API
// Import the module and reference it with the alias vscode in your code below
import * as vscode from "vscode";
import * as path from "path";
import { compile, getFix } from "./util";
import { CodelensProvider } from "./code-lens/codeLensProvider";
import { Decorator } from "./decorator/decorator";

import * as t from "./types";
import * as c from "./constants";

let disposables: vscode.Disposable[] = [];
let eventDisposables: vscode.Disposable[] = [];

// file-wise history store
export let docStore: Map<string, t.DocumentStore>;

async function compileAndGetFixHelper(): Promise<t.Fix> {
  // TODO: What if user changes tab immediately? - activeEditor changes - cancellation token?
  //* Or find an alternate way to get fullText of document and simply pass document along
  const activeEditor = vscode.window.activeTextEditor;

  if (activeEditor !== undefined) {
    const document = activeEditor.document;
    const cursorPosition = activeEditor.selection.active;
    const filePath = document.uri.fsPath;
    let result: t.Fix = undefined;

    console.log(`Compiling ${filePath}`);
    const compiled = await compile(filePath);

    if (!compiled) {
      console.log("Syntax Error -> Preparing and Sending data...");

      const data: t.Payload = {
        // srcCode: getDocumentText( document ),
        source: document.getText(),
        lastEditLine: cursorPosition.line,
      };
      const payload: t.Payload = JSON.parse(JSON.stringify(data));

      if (c.baseURL === undefined) {
        console.log("Web Server path invalid");
        return undefined;
      } else {
        result = await getFix(c.baseURL!, payload);
        if (result !== undefined) {
          console.log("Reply from Server:");
        }
      }
    }

    return result;
  }
}

async function compileAndGetFix(
  document: vscode.TextDocument,
  docStore: Map<string, t.DocumentStore>
): Promise<t.Fix> {
  const filePath = document.uri.fsPath;
  let fixes: t.Fix = undefined;
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

export function activate(context: vscode.ExtensionContext) {
  console.log("Extension 'python-hints' is now active!");

  docStore = new Map();
  const decorator: Decorator = new Decorator();

  disposables.push(
    vscode.commands.registerCommand(
      "python-hints.toggleHints",
      async function () {
        console.log("toggleFix Command triggered...");

        const flag = vscode.workspace
          .getConfiguration("python-hints")
          .get("enableCodeLens", false);
        vscode.workspace
          .getConfiguration("python-hints")
          .update("enableCodeLens", !flag, true);

        // TODO: Decide when to trigger execution of backend
        const activeEditor = vscode.window.activeTextEditor;
        if (activeEditor !== undefined) {
          // vscode.workspace.getConfiguration( "python-hints" ).update( "enableCodeLens", true, true );
          // the save event will itself handle compilation and fix suggestions
          if (activeEditor.document.isDirty) {
            activeEditor.document.save();
          } else {
            // document.save() doesn't trigger if document isn't dirty
            const fixes = await compileAndGetFix(
              activeEditor.document,
              docStore
            );

            console.log(fixes);
          }
        }
      }
    )
  );

  disposables.push(
    vscode.commands.registerCommand(
      "python-hints.toggleHighlight",
      async function () {
        let flag: number = vscode.workspace
          .getConfiguration("python-hints")
          .get("activeHighlight", 0);
        flag = (flag + 1) % 3;
        vscode.workspace
          .getConfiguration("python-hints")
          .update("activeHighlight", flag, true);

        let diagnosticLevel = 1;
        if (flag === 2) {
          diagnosticLevel = 3;
        }
        vscode.workspace
          .getConfiguration("python-hints")
          .update("diagnosticLevel", diagnosticLevel, true);

        // Accomodate delay in propagating above configuration
        setTimeout(() => {
          decorator.updateDecorations();
        }, 300);
        // decorator.updateDecorations();
      }
    )
  );

  decorator.registerDecorator(context);

  eventDisposables.push(
    vscode.workspace.onWillSaveTextDocument(async (saveEvent) => {
      console.log("Document Saved...");

      // TODO: Need to distinguish first time save from rest? - as it captures wrong name (Untitled*) - how to then check the file after saving? - another event?
      if (
        saveEvent.reason === vscode.TextDocumentSaveReason.Manual &&
        path.basename(saveEvent.document.uri.fsPath.split(".")[1]) === "py"
      ) {
        const fixes = await compileAndGetFix(saveEvent.document, docStore);

        console.log(fixes);
        decorator.updateDecorations();
      }
    })
  );

  disposables.push(
    vscode.languages.registerCodeLensProvider("python", new CodelensProvider())
  );

  disposables.push(
    vscode.commands.registerCommand("python-hints.codelensAction", () => {
      vscode.window.showInformationMessage("CodeLens action");
    })
  );

  disposables.forEach((item) => context.subscriptions.push(item));

  eventDisposables.forEach((item) => context.subscriptions.push(item));
}

export function deactivate() {
  if (disposables) {
    disposables.forEach((item) => item.dispose());
  }
  if (eventDisposables) {
    eventDisposables.forEach((item) => item.dispose());
  }

  disposables = [];
  eventDisposables = [];
}
