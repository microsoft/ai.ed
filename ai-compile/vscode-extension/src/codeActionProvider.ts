import * as vscode from "vscode";
import * as path from "path";

import * as pymacer from "./pymacer";
import { documentStore } from "./extension";

export enum FeedbackLevel {
  novice,
  expert
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

  /* This function helps modify the default range for a fix returned by pymacer.
   * The range is used, to underline with squiggly lines, for indicating errors to the user.
  */
  public getCustomRange(
     document: vscode.TextDocument, 
     fix: pymacer.Response,
     edit: pymacer.Edit
     ): vscode.Range | undefined {

    let customRange: vscode.Range | undefined;
    let startPos = new vscode.Position(fix.lineNo, edit.start);
    let endPos = new vscode.Position(fix.lineNo, edit.end + 1);
  
    let lineText = document.lineAt(fix.lineNo).text;
    lineText = lineText.slice(edit.start);
    const lineStartCharCode = lineText.charCodeAt(0);
    
    // capture range of next word (in case of a starting whitespace (WS) character - typical of indentation fixes)
    if(lineStartCharCode === " ".charCodeAt(0)) {
      
      const alphaNumRegExp = /[a-z0-9_]+/ig;
      let match = alphaNumRegExp.exec(lineText);
      // capture range of next alphaNumeric word
      if(match !== null) {
        startPos = new vscode.Position(fix.lineNo, match!.index + edit.start);
        endPos = new vscode.Position(fix.lineNo, alphaNumRegExp!.lastIndex + edit.start);
      } else {
        // assuming line is non-empty
        const nonWSRegExp = /[^\s]+/ig;
        match = nonWSRegExp.exec(lineText);
        startPos = new vscode.Position(fix.lineNo, match!.index + edit.start);
        endPos = new vscode.Position(fix.lineNo, nonWSRegExp!.lastIndex + edit.start);
      }
      customRange = new vscode.Range(startPos, endPos);

    } else {  // if line starts with non-WS character
      
        let isAlphaNum = (charCode: number) => {
          return !(!(charCode > 47 && charCode < 58) && // (0-9)
          !(charCode > 64 && charCode < 91) && // (A-Z)
          !(charCode > 96 && charCode < 123)); // (a-z)
        };

        if(isAlphaNum(lineStartCharCode)) {
          // capture range of entire word (instead of a single alphaNumeric character)
          customRange = document.getWordRangeAtPosition(startPos);
        } else {
          // capture range of only a single character (in case of non-alphaNum starting character)
          customRange = new vscode.Range(startPos, endPos);
        }

    }

    return customRange;

  }

  // updates code actions for the document
  public update(
    document: vscode.TextDocument
  ) {

    if(document) {
      const filePathNameInParts = path.basename(document.uri.fsPath).split('.');
      const fileExtension = filePathNameInParts[filePathNameInParts.length-1];
      if (
        vscode.workspace
        .getConfiguration("python-hints")
        .get("enableDiagnostics", true) &&
        fileExtension === "py"
      ) {

        // diagnosticLevel is an indicator to choosing a particular feedback level 
        this.feedbackLevel = vscode.workspace
        .getConfiguration("python-hints")
        .get("diagnosticLevel", 0);

        let diagnostics: {
          code: string;
          message: string;
          range: vscode.Range;
          severity: vscode.DiagnosticSeverity;
          source: string;
        }[] = [];
        
        const fixes: pymacer.Fixes = documentStore.get(document.uri.fsPath)?.fixes;
        fixes?.forEach((fix) => {
          let i = 0;
          fix.editDiffs?.forEach((edit) => {
            let diagnosticMsg: string = "";
            if(this.feedbackLevel === FeedbackLevel.novice) {
              diagnosticMsg = fix.feedback[i].fullText;
            } else if(this.feedbackLevel === FeedbackLevel.expert) {
              diagnosticMsg = fix.repairClasses[i];
            }
            i++;
            const editRange = this.getCustomRange(document, fix, edit);
            diagnostics.push({
              code: "",
              message: diagnosticMsg ?? "Error in this line",
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

    let codeActionMsg: string = "Apply misc. repairs";
    if(fix !== undefined ) {
      const edit = fix?.editDiffs[0];      
      if(edit !== undefined) {
        let srcText = document.lineAt(fix.lineNo).text;
        const trgtText = edit.insertString;
        if(edit.type === "replace") {
          srcText = srcText.slice(edit.start, edit.end + 1);
          codeActionMsg = "Replace '" + srcText + "' with '" + trgtText + "'";
        } else if(edit.type === "insert") {
            srcText = srcText.slice(diagnostic.range.start.character, diagnostic.range.end.character);
            codeActionMsg = "Insert '" + trgtText + "' before '" + srcText + "'";
        } else if(edit.type === "delete") {
            srcText = srcText.slice(edit.start, edit.end + 1);
            codeActionMsg = "Delete '" + srcText + "'";
        }
      }
    }

    const action = new vscode.CodeAction(
      codeActionMsg,
      vscode.CodeActionKind.QuickFix
    );

    action.diagnostics = [diagnostic];
    action.isPreferred = true;

    action.edit = new vscode.WorkspaceEdit();

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
