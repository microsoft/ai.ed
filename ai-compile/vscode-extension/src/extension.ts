import * as vscode from "vscode";
import * as path from "path";
import * as fs from "fs";

import { Decorator } from "./decorator";
import { EduCodeActionProvider } from "./codeActionProvider";
import * as pymacer from "./pymacer";
import { isPythonFile } from "./util";

let disposables: vscode.Disposable[] = [];
let eventDisposables: vscode.Disposable[] = [];

export enum DisplayDiagnosticLevel {
  none,
  novice,
  expert
}

// stores file-wise history of fixes
export let documentStore: Map<string, pymacer.DocumentStore>;

export let setTimeOut: number;
export let requestTimeOut: number;
export let shellCmdTimeOut: number;

export function readConfigFile(
  property: string
): any {

  let retVal = undefined;
  let extensionPackageJson: string = fs.readFileSync( path.resolve( __dirname,
      "../data/pyedu-config.json" ), "utf8" );
  let extensionPackage = JSON.parse( extensionPackageJson );
  if( extensionPackage.hasOwnProperty( property ) ) {
      retVal = extensionPackage[ property ];
  }
  return retVal;

}

function initExtensionConfiguration() {

  try {
    const displayUpdate = readConfigFile("displayUpdate");
    setTimeOut = displayUpdate["setTimeOut"];

    const commandExecution = readConfigFile("commandExecution");
    requestTimeOut = commandExecution["requestTimeOut"];
    shellCmdTimeOut = commandExecution["shellCmdTimeOut"];
    
    const defaultConfigProperties = readConfigFile("defaultConfigProperties");
    const enableCodeLens = defaultConfigProperties["enableCodeLens"] === "true";
    const webServerPath = defaultConfigProperties["webServerPath"];
    const diagnosticLevel = parseInt(defaultConfigProperties["diagnosticLevel"]);
    const enableDiagnostics = defaultConfigProperties["enableDiagnostics"] === "true";
    const activeHighlight = parseInt(defaultConfigProperties["activeHighlight"]);

    vscode.workspace
    .getConfiguration("python-hints")
    .update("enableCodeLens", enableCodeLens, true);
    vscode.workspace
    .getConfiguration("python-hints")
    .update("webServerPath", webServerPath, true);
    vscode.workspace
    .getConfiguration("python-hints")
    .update("diagnosticLevel", diagnosticLevel, true);
    vscode.workspace
    .getConfiguration("python-hints")
    .update("enableDiagnostics", enableDiagnostics, true);
    vscode.workspace
    .getConfiguration("python-hints")
    .update("activeHighlight", activeHighlight, true);

  } catch {
    console.log("Missing/ Corrupt pyedu-config.json");
  }

}

export function activate(context: vscode.ExtensionContext) {

  console.log("Extension 'python-hints' is now active!");

  initExtensionConfiguration();

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
            if(fixes !== undefined) {
              console.log(fixes);
            } else {
              console.log("PyMACER couldn't diagnose any errors ");
            }
            setTimeout(() => {
              eduCodeActionProvider.update(vscode.window.activeTextEditor!.document);
            }, setTimeOut);
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
          .get("activeHighlight", DisplayDiagnosticLevel.none);
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
            }, setTimeOut);
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
          .get("diagnosticLevel", DisplayDiagnosticLevel.none);
          diagnosticLevel = (diagnosticLevel + 1) % 2;
        vscode.workspace
          .getConfiguration("python-hints")
          .update("diagnosticLevel", diagnosticLevel, true);
      }));

  decorator.registerDecorator(context);

  eventDisposables.push(
    vscode.workspace.onWillSaveTextDocument(async (saveEvent) => {
      console.log("Document Saved...");

      if (
        saveEvent.reason === vscode.TextDocumentSaveReason.Manual &&
        isPythonFile(saveEvent.document)
      ) {
        const fixes = await pymacer.compileAndGetFix(
          saveEvent.document,
          documentStore
        );

        console.log(fixes);
        decorator.updateDecorations();
        setTimeout(() => {
          eduCodeActionProvider.update(vscode.window.activeTextEditor!.document);
        }, setTimeOut);
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
