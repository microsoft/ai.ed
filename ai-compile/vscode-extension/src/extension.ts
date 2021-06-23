import * as vscode from "vscode";
import * as path from "path";

import { Decorator } from "./decorator";
import { EduCodeActionProvider } from "./codeActionProvider";
import * as pymacer from "./pymacer";

let disposables: vscode.Disposable[] = [];
let eventDisposables: vscode.Disposable[] = [];

// stores file-wise history of fixes
export let documentStore: Map<string, pymacer.DocumentStore>;

export function activate(context: vscode.ExtensionContext) {

  console.log("Extension 'python-hints' is now active!");

  documentStore = new Map();
  const decorator: Decorator = new Decorator();

  let eduCodeActionProvider = new EduCodeActionProvider();

  let codeActionProvider = vscode.languages.registerCodeActionsProvider(
    "python",
    eduCodeActionProvider,
    { providedCodeActionKinds: EduCodeActionProvider.providedCodeActionKinds }
  );

  disposables.push(codeActionProvider);

  disposables.push(
    vscode.commands.registerCommand(
      "python-hints.toggleHints",
      async function () {
        console.log("toggleHints Command triggered...");

        const enableDiagnostics = vscode.workspace
          .getConfiguration("python-hints")
          .get("enableDiagnostics", false);
        vscode.workspace
          .getConfiguration("python-hints")
          .update("enableDiagnostics", !enableDiagnostics, true);

        const activeEditor = vscode.window.activeTextEditor;
        if (activeEditor !== undefined) {
          // the save event will itself handle compilation and fix suggestions
          if (activeEditor.document.isDirty) {
            activeEditor.document.save();
          } else {
            // document.save() doesn't trigger if document isn't dirty
            const fixes = await pymacer.compileAndGetFix(
              activeEditor.document,
              documentStore
            );

            console.log(fixes);
            // TODO: What is the right amount of time to allow the previous configuration propagation?
            setTimeout(() => {
              eduCodeActionProvider.update(vscode.window.activeTextEditor!.document);
            }, 300);
          }
        }
      }
    )
  );

  disposables.push(
    vscode.commands.registerCommand(
      "python-hints.toggleHighlight",
      async function () {
        let activeHighlight: number = vscode.workspace
          .getConfiguration("python-hints")
          .get("activeHighlight", 0);
          activeHighlight = (activeHighlight + 1) % 3;
        vscode.workspace
          .getConfiguration("python-hints")
          .update("activeHighlight", activeHighlight, true);

        const activeEditor = vscode.window.activeTextEditor;
        if (activeEditor !== undefined) {
          // the save event will itself handle compilation and fix suggestions
          if (activeEditor.document.isDirty) {
            activeEditor.document.save();
          } else {
            // document.save() doesn't trigger if document isn't dirty
            const fixes = await pymacer.compileAndGetFix(
              activeEditor.document,
              documentStore
            );

            console.log(fixes);
            // Accomodate delay in propagating above configuration
            setTimeout(() => {
              decorator.updateDecorations();
            }, 300);
          }
        }
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
      const fileExtension = filePathParts[filePathParts.length-1];
      // TODO: Need to distinguish first time save from rest? - as it captures wrong name (Untitled*) - how to then check the file after saving? - another event?
      if (
        saveEvent.reason === vscode.TextDocumentSaveReason.Manual &&
        fileExtension === "py"
      ) {
        const fixes = await pymacer.compileAndGetFix(
          saveEvent.document,
          documentStore
        );

        console.log(fixes);
        decorator.updateDecorations();
        setTimeout(() => {
          eduCodeActionProvider.update(vscode.window.activeTextEditor!.document);
        }, 300);
      }
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
