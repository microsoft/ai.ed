// The module 'vscode' contains the VS Code extensibility API
// Import the module and reference it with the alias vscode in your code below
import * as vscode from "vscode";

import * as path from "path";
import { CodelensProvider } from "./codeLensProvider";
import { Decorator } from "./decorator";

import * as pymacer from "./pymacer";

let disposables: vscode.Disposable[] = [];
let eventDisposables: vscode.Disposable[] = [];

// file-wise history store
export let docStore: Map<string, pymacer.DocumentStore>;

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
            const fixes = await pymacer.compileAndGetFix(
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
        const fixes = await pymacer.compileAndGetFix(
          saveEvent.document,
          docStore
        );

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
