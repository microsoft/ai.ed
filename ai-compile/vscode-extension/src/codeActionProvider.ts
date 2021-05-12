import * as vscode from "vscode";
import * as path from "path";

import * as pymacer from "./pymacer";

export let diagnosticCollection = vscode.languages.createDiagnosticCollection(
  "pythonedu"
);

export function updateDiagnostics(
  document: vscode.TextDocument,
  fixes: pymacer.Fixes
) {
  if (document && path.basename(document.uri.fsPath) === "rainfall.py") {
    diagnosticCollection.set(document.uri, [
      {
        code: "PYEDU_MACER",
        message:
          "🤗 Python couldn't understand your program.\n\n" +
          "PUT ERROR MESSAGE HERE",
        range: new vscode.Range(
          new vscode.Position(6, 12),
          new vscode.Position(6, 27)
        ),
        severity: vscode.DiagnosticSeverity.Warning,
        source: "PyEdu 🐍",
      },
    ]);
  } else {
    diagnosticCollection.clear();
  }
}

export class EduCodeActionProvider implements vscode.CodeActionProvider {
  public static readonly providedCodeActionKinds = [
    vscode.CodeActionKind.QuickFix,
  ];

  private createFix(diagnostic: vscode.Diagnostic): vscode.CodeAction {
    const action = new vscode.CodeAction(
      "Replace x with y",
      vscode.CodeActionKind.QuickFix
    );

    action.diagnostics = [diagnostic];
    action.isPreferred = true;

    return action;
  }

  provideCodeActions(
    document: vscode.TextDocument,
    range: vscode.Range | vscode.Selection,
    context: vscode.CodeActionContext,
    token: vscode.CancellationToken
  ): vscode.CodeAction[] {
    for (let x of context.diagnostics) {
      console.log(x);
    }

    return context.diagnostics
      .filter((diagnostic) => diagnostic.code === "PYEDU_MACER")
      .map((diagnostic) => this.createFix(diagnostic));
  }
}
