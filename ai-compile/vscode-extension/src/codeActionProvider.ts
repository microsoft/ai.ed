import * as vscode from "vscode";
import * as path from "path";

import * as pymacer from "./pymacer";

export enum FeedbackLevel {
  Novice,
  Expert,
}

export class EduCodeActionProvider implements vscode.CodeActionProvider {
  public static readonly providedCodeActionKinds = [
    vscode.CodeActionKind.QuickFix,
  ];

  public diagnosticCollection = vscode.languages.createDiagnosticCollection(
    "pythonedu"
  );

  public codeActions: Map<vscode.Diagnostic, vscode.CodeAction> = new Map();
  public createDiagnostics: boolean = true;
  public createCodeActions: boolean = true;
  public feedbackLevel = FeedbackLevel.Novice;

  public update(document: vscode.TextDocument, fixes: pymacer.Fixes) {
    if (document && path.basename(document.uri.fsPath) === "rainfall.py") {
      // TODO: You will need to populate an array of diagnostics. For each
      // diagnostic, you will also need to call createFix() and use it's
      // return value to populate this.codeActions.
      const diagnostics = [
        {
          code: "",
          message:
            "😞 Python couldn't understand your program.\n\n" +
            "Should this be something other than 'else'?",
          range: new vscode.Range(
            new vscode.Position(11, 4),
            new vscode.Position(11, 8)
          ),
          severity: vscode.DiagnosticSeverity.Warning,
          source: "PyEdu 🐍",
        },
      ];

      this.diagnosticCollection.set(document.uri, diagnostics);

      if (this.createCodeActions) {
        let codeAction = this.createFix(document, diagnostics[0], undefined);
        this.codeActions.set(diagnostics[0], codeAction);
      }
    } else {
      this.diagnosticCollection.clear();
    }
  }

  // TODO: You need to fill this in with a repair.
  private createFix(
    document: vscode.TextDocument,
    diagnostic: vscode.Diagnostic,
    fix: pymacer.Response | undefined
  ): vscode.CodeAction {
    const action = new vscode.CodeAction(
      "Replace 'else' with 'elif'",
      vscode.CodeActionKind.QuickFix
    );

    action.diagnostics = [diagnostic];
    action.isPreferred = true;

    action.edit = new vscode.WorkspaceEdit();

    // TODO: Now use action.edit.replace, action.edit.set, etc. to make your quick fix.
    // action.edit.
    // action.edit.replace(document.uri, new vscode.Range(range.start, range.start.translate(0, 2)), "REPLACEMENT");

    return action;
  }

  public provideCodeActions(
    document: vscode.TextDocument,
    range: vscode.Range | vscode.Selection,
    context: vscode.CodeActionContext,
    token: vscode.CancellationToken
  ): vscode.CodeAction[] {
    let codeActions = [];
    for (let diagnostic of context.diagnostics) {
      let codeAction = this.codeActions.get(diagnostic);
      if (codeAction) {
        codeActions.push(codeAction);
      }
    }

    return codeActions;
  }
}
