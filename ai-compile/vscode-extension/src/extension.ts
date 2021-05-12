// The module 'vscode' contains the VS Code extensibility API
// Import the module and reference it with the alias vscode in your code below
import * as vscode from "vscode";

import { EduCodeActionProvider, FeedbackLevel } from "./codeActionProvider";
import * as pymacer from "./pymacer";

let disposables: vscode.Disposable[] = [];
let eventDisposables: vscode.Disposable[] = [];

// file-wise history store
export let docStore: Map<string, pymacer.DocumentStore>;

export function activate(context: vscode.ExtensionContext) {
  console.log("Extension 'python-hints' is now active!");

  docStore = new Map();
  let eduCodeActionProvider = new EduCodeActionProvider();

  let codeActionProvider = vscode.languages.registerCodeActionsProvider(
    "python",
    eduCodeActionProvider,
    { providedCodeActionKinds: EduCodeActionProvider.providedCodeActionKinds }
  );

  let pythonHintLevelCommand = vscode.commands.registerCommand(
    "eduai.hintLevel",
    async () => {
      const pick = await vscode.window.showQuickPick(
        ["Beginner (Learning-oriented)", "Expert (Repair-oriented)"],
        {
          placeHolder: "Select the style of feedback",
          onDidSelectItem: (item) => {},
        }
      );

      // This will be undefined is there is no selection.      
      if (pick === 'Beginner (Learning-oriented)') {
        console.log(`Feedback style: ${pick}`);
        eduCodeActionProvider.feedbackLevel = FeedbackLevel.novice;

        if (vscode.window.activeTextEditor) {
          eduCodeActionProvider.update(vscode.window.activeTextEditor.document, []);
        }
      }
      else if (pick === 'Expert (Repair-oriented)') {
        console.log(`Feedback style: ${pick}`);
        eduCodeActionProvider.feedbackLevel = FeedbackLevel.expert;

        if (vscode.window.activeTextEditor) {
          eduCodeActionProvider.update(vscode.window.activeTextEditor.document, []);
        }
      }      
    }
  );


  context.subscriptions.push(pythonHintLevelCommand);

  // TODO: This isn't the correct place to call eduActionProvider, but demonstrates
  // the update call.
  if (vscode.window.activeTextEditor) {
    eduCodeActionProvider.update(vscode.window.activeTextEditor.document, []);
  }

  context.subscriptions.push(vscode.workspace.onDidChangeTextDocument(e => {
    console.log("Active editor did change.");
		if (e) {
			eduCodeActionProvider.update(e.document, []);
		}
	}));

  disposables.push(codeActionProvider);
}
