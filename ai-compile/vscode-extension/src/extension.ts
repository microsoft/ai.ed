// The module 'vscode' contains the VS Code extensibility API
// Import the module and reference it with the alias vscode in your code below
import * as vscode from "vscode";

import * as path from "path";
import { CodelensProvider } from "./codeLensProvider";
import { Decorator } from "./decorator";

import { EduCodeActionProvider } from "./codeActionProvider";
import * as pymacer from "./pymacer";

let disposables: vscode.Disposable[] = [];
let eventDisposables: vscode.Disposable[] = [];

// file-wise history store
export let docStore: Map<string, pymacer.DocumentStore>;

export function activate(context: vscode.ExtensionContext) {
  console.log("Extension 'python-hints' is now active!");

  docStore = new Map();
  const decorator: Decorator = new Decorator();

  let eduCodeActionProvider = new EduCodeActionProvider();

  let codeActionProvider = vscode.languages.registerCodeActionsProvider(
    "python",
    eduCodeActionProvider,
    { providedCodeActionKinds: EduCodeActionProvider.providedCodeActionKinds }
  );

  // TODO: This isn't the correct place to call eduActionProvider, but demonstrates
  // the update call.
  // if (vscode.window.activeTextEditor) {
  //   eduCodeActionProvider.update(vscode.window.activeTextEditor.document, []);
  // }

  disposables.push(codeActionProvider);

  disposables.push(
    vscode.commands.registerCommand(
      "python-hints.toggleHints",
      async function () {
        console.log("toggleHints Command triggered...");

        /*
        const flag = vscode.workspace
          .getConfiguration("python-hints")
          .get("enableCodeLens", false);
        vscode.workspace
          .getConfiguration("python-hints")
          .update("enableCodeLens", !flag, true);
          */

        const flag = vscode.workspace
          .getConfiguration("python-hints")
          .get("enableDiagnostics", false);
        vscode.workspace
          .getConfiguration("python-hints")
          .update("enableDiagnostics", !flag, true);

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
            // if (vscode.window.activeTextEditor) {
              // TODO: What is the right amount of time to allow configuration propagation?
              setTimeout(() => {
                eduCodeActionProvider.update(vscode.window.activeTextEditor!.document, fixes);
              }, 300);
            // }
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

  disposables.push(
    vscode.commands.registerCommand(
      "python-hints.toggleDiagnosticLevel",
      async function () {
        let diagnosticLevel: number = vscode.workspace
          .getConfiguration("python-hints")
          .get("diagnosticLevel", 0);
          diagnosticLevel = (diagnosticLevel + 1) % 2;
        vscode.workspace
          .getConfiguration("python-hints")
          .update("diagnosticLevel", diagnosticLevel, true);
      }));

  decorator.registerDecorator(context);

  eventDisposables.push(
    vscode.workspace.onWillSaveTextDocument(async (saveEvent) => {
      console.log("Document Saved...");

      const filePathParts = path.basename(saveEvent.document.uri.fsPath).split(".");
      const fileExt = filePathParts[filePathParts.length-1];
      // TODO: Need to distinguish first time save from rest? - as it captures wrong name (Untitled*) - how to then check the file after saving? - another event?
      if (
        saveEvent.reason === vscode.TextDocumentSaveReason.Manual &&
        fileExt === "py"
      ) {
        const fixes = await pymacer.compileAndGetFix(
          saveEvent.document,
          docStore
        );

        console.log(fixes);
        decorator.updateDecorations();
        // if (vscode.window.activeTextEditor) {
          setTimeout(() => {
            eduCodeActionProvider.update(vscode.window.activeTextEditor!.document, fixes);
          }, 300);
        // }
      }
  })
  );

  /*
  disposables.push(
    vscode.languages.registerCodeLensProvider("python", new CodelensProvider())
  );

  disposables.push(
    vscode.commands.registerCommand("python-hints.codelensAction", () => {
      vscode.window.showInformationMessage("CodeLens action");
    })
  );
  */

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
