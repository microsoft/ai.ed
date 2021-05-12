import * as vscode from "vscode";
import * as path from "path";

import * as pymacer from "./pymacer";
import { docStore } from "./extension";

export enum FeedbackLevel {
  novice,
  expert,
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
  public feedbackLevel = FeedbackLevel.novice;

  public update(document: vscode.TextDocument, fixes: pymacer.Fixes) {
    if(document) {
      const fileNameParts = path.basename(document.uri.fsPath).split('.');
      const fileExt = fileNameParts[fileNameParts.length-1];
      if (path.basename(document.uri.fsPath).split(".")[1] === "py") {
        const diagnosticLevel: number = vscode.workspace
        .getConfiguration("python-hints")
        .get("diagnosticLevel", 0);

        let diagnostics: {
          code: string;
          message: string;
          range: vscode.Range;
          severity: vscode.DiagnosticSeverity;
          source: string;
        }[] = [];

        // const diagnosticFlag: number = vscode.workspace
        // .getConfiguration("python-hints")
        // .get("activeHighlight", 0);

        // if (diagnosticFlag > 0) {
        if(this.feedbackLevel === FeedbackLevel.novice) {
          const fixes: pymacer.Fixes = docStore.get(document.uri.fsPath)?.fixes;
          fixes?.forEach((fix) => {
            let diagnosticMsg: string = "";
            switch (diagnosticLevel) {
              case 1: {
                diagnosticMsg = fix.feedback[0].fullText;
                break;
              }
              case 2: {
                diagnosticMsg = fix.repairClasses[0];
                break;
              }
              case 3: {
                diagnosticMsg = fix.feedback[0].fullText;
                break;
              }
            }
            // TODO?: Handle case of multiple errors/ edits on single line
            fix.editDiffs?.forEach((edit) => {
              const startPos = new vscode.Position(fix.lineNo, edit.start);
              const endPos = new vscode.Position(fix.lineNo, edit.end + 1);
              const editRange = new vscode.Range(startPos, endPos);
              // const editRange = edit.type === "insert" ?
              //   document.getWordRangeAtPosition(startPos):
              //   new vscode.Range(startPos, endPos);
              // let editRange: vscode.Range | undefined;
              // if (edit.type === "insert") {
              //   editRange = document.getWordRangeAtPosition(startPos);
              // } else {
              //   editRange = new vscode.Range(startPos, endPos);
              // }
              diagnostics.push({
                code: "",
                message: diagnosticMsg,
                range: editRange!,
                severity: vscode.DiagnosticSeverity.Warning,
                source: "PyEdu 🐍",
              });
              if (this.createCodeActions) {
                let codeAction = this.createFix(document, diagnostics[diagnostics.length-1], fix);
                this.codeActions.set(diagnostics[diagnostics.length-1], codeAction);
              }
            });
          });
        }

        this.diagnosticCollection.set(document.uri, diagnostics);


      } else {
        this.diagnosticCollection.clear();
      }
    }
  }

  private createFix(
    document: vscode.TextDocument,
    diagnostic: vscode.Diagnostic,
    fix: pymacer.Response | undefined
  ): vscode.CodeAction {
    const action = new vscode.CodeAction(
      fix === undefined ? "" : fix.repairLine,
      vscode.CodeActionKind.QuickFix
    );

    action.diagnostics = [diagnostic];
    action.isPreferred = true;

    action.edit = new vscode.WorkspaceEdit();

    // if(fix !== undefined) {
    //   const position = new vscode.Position(fix!.lineNo, 0);
    //   const editRange = document.getWordRangeAtPosition(position, new RegExp('.+'));
    //   action.edit.replace(document.uri, editRange!, fix.repairLine);
    // }

    fix?.editDiffs?.forEach((edit) => {
      const startPos = new vscode.Position(fix.lineNo, edit.start);
      const endPos = new vscode.Position(fix.lineNo, edit.end + 1);
      const editRange = new vscode.Range(startPos, endPos);
      if (edit.type === "insert") {
        action.edit?.insert(document.uri, startPos, edit.insertString);
      } else if (edit.type === "delete") {
          action.edit?.delete(document.uri, editRange);
      } else {
          action.edit?.replace(document.uri, editRange, edit.insertString);
      }
    });
    

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
