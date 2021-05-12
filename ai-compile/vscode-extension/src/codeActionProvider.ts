import * as vscode from "vscode";
import * as path from "path";

import * as pymacer from "./pymacer";

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

  private updateForNovices(document: vscode.TextDocument) {
    console.log("Updating novice diagnostics.");

    // Clear all the code actions.
    this.codeActions.clear();

    let line = "";
    const diagnostics: vscode.Diagnostic[] = [];

    // Check for => issue.
    line = document.lineAt(5).text;
    if (line.includes("if day => 0:")) {
      const diagnostic = {
        code: "",
        message:
          "😞 Python couldn't understand your program.\n\n" +
          "Look more closely at '=>'. Python doesn't recognize this comparison operator.",
        range: new vscode.Range(
          new vscode.Position(5, 15),
          new vscode.Position(5, 17)
        ),
        severity: vscode.DiagnosticSeverity.Warning,
        source: "PyEdu 🐍",
      };

      const action = new vscode.CodeAction(
        "Learn more about comparison operators",
        vscode.CodeActionKind.Empty
      );

      action.command = {
        command: "vscode.open",
        title: "",
        arguments: [
          vscode.Uri.parse(
            "https://docs.python.org/3/reference/expressions.html#comparisons"
          ),
        ],
      };
      action.diagnostics = [diagnostic];

      this.codeActions.set(diagnostic, action);
      diagnostics.push(diagnostic);
    }

    // BEGIN: ASSIGN TO RIGHT
    line = document.lineAt(6).text;
    if (line.includes("sum + day = sum")) {
      const diagnostic = {
        code: "",
        message:
          "😞 Python couldn't understand your program.\n\n" +
          "Look more closely at the left and right sides of assignment statement (=).",
        range: new vscode.Range(
          new vscode.Position(6, 12),
          new vscode.Position(6, 28)
        ),
        severity: vscode.DiagnosticSeverity.Warning,
        source: "PyEdu 🐍",
        relatedInformation: [
          new vscode.DiagnosticRelatedInformation(
            new vscode.Location(
              document.uri,
              new vscode.Range(
                new vscode.Position(7, 12),
                new vscode.Position(7, 30)
              )
            ),
            "Hint: You've done it correctly on line 8. 🙂"
          ),
        ],
      };

      const action = new vscode.CodeAction(
        "Learn more about assignment",
        vscode.CodeActionKind.Empty
      );

      action.command = {
        command: "vscode.open",
        title: "",
        arguments: [
          vscode.Uri.parse(
            "http://anh.cs.luc.edu/handsonPythonTutorial/variables.html"
          ),
        ],
      };
      action.diagnostics = [diagnostic];
      // END: ASSIGN TO RIGHT

      this.codeActions.set(diagnostic, action);
      diagnostics.push(diagnostic);

      console.log("sum + day");
    }

    // Check for else.
    line = document.lineAt(11).text;
    if (line.includes("else")) {
      const diagnostic = {
        code: "",
        message:
          "😞 Python couldn't understand your program.\n\n" +
          "Try changing 'else' to something different. Recall the differences between 'if', 'elif', and 'else'.",
        range: new vscode.Range(
          new vscode.Position(11, 4),
          new vscode.Position(11, 8)
        ),
        severity: vscode.DiagnosticSeverity.Warning,
        source: "PyEdu 🐍",
      };

      const action = new vscode.CodeAction(
        "Learn more about control flow statements",
        vscode.CodeActionKind.Empty
      );

      action.command = {
        command: "vscode.open",
        title: "",
        arguments: [
          vscode.Uri.parse(
            "https://docs.python.org/3/tutorial/controlflow.html"
          ),
        ],
      };
      action.diagnostics = [diagnostic];

      this.codeActions.set(diagnostic, action);
      diagnostics.push(diagnostic);
      console.log("else");
    }

    // Check for missing comma in print.
    line = document.lineAt(15).text;
    if (line.includes('print("Average:" avg)')) {
      const diagnostic = {
        code: "",
        message:
          "😞 Python couldn't understand your program.\n\n" +
          "It looks like you are trying to call the 'print' function with multiple arguments. What do arguments need to be separated by?",
        range: new vscode.Range(
          new vscode.Position(15, 16),
          new vscode.Position(15, 17)
        ),
        severity: vscode.DiagnosticSeverity.Warning,
        source: "PyEdu 🐍",
      };

      const action = new vscode.CodeAction(
        "Learn more about function arguments",
        vscode.CodeActionKind.Empty
      );

      action.command = {
        command: "vscode.open",
        title: "",
        arguments: [
          vscode.Uri.parse(
            "https://docs.python.org/3/library/functions.html#print"
          ),
        ],
      };

      this.codeActions.set(diagnostic, action);
      diagnostics.push(diagnostic);
      console.log("print");
    }

    this.diagnosticCollection.set(document.uri, diagnostics);
  }

  private updateForExperts(document: vscode.TextDocument) {
    // Clear all the code actions.
    this.codeActions.clear();

    let line = "";
    const diagnostics: vscode.Diagnostic[] = [];

    // Check for => issue.
    line = document.lineAt(5).text;
    if (line.includes("if day => 0:")) {
      const diagnostic = {
        code: "",
        message: "Found: =>\nExpected: >=",
        range: new vscode.Range(
          new vscode.Position(5, 15),
          new vscode.Position(5, 17)
        ),
        severity: vscode.DiagnosticSeverity.Error,
        source: "PyEdu 🚀",
      };

      const action = new vscode.CodeAction(
        "Replace '=>' with '>='",
        vscode.CodeActionKind.QuickFix
      );

      action.edit = new vscode.WorkspaceEdit();
      action.edit.replace(
        document.uri,
        new vscode.Range(
          new vscode.Position(5, 15),
          new vscode.Position(5, 17)
        ),
        ">="
      );

      action.diagnostics = [diagnostic];

      this.codeActions.set(diagnostic, action);
      diagnostics.push(diagnostic);
    }

    // BEGIN: ASSIGN TO RIGHT
    line = document.lineAt(6).text;
    if (line.includes("sum + day = sum")) {
      const diagnostic = {
        code: "",
        message: "Found: sum + day = sum\nExpected: sum = sum + day",
        range: new vscode.Range(
          new vscode.Position(6, 12),
          new vscode.Position(6, 28)
        ),
        severity: vscode.DiagnosticSeverity.Error,
        source: "PyEdu 🚀",
      };

      const action = new vscode.CodeAction(
        "Replace 'sum + day = sum' with 'sum = sum + day'",
        vscode.CodeActionKind.QuickFix
      );

      action.edit = new vscode.WorkspaceEdit();
      action.edit.replace(
        document.uri,
        new vscode.Range(
          new vscode.Position(6, 12),
          new vscode.Position(6, 28)
        ),
        "sum = sum + day"
      );

      action.diagnostics = [diagnostic];
      // END: ASSIGN TO RIGHT

      this.codeActions.set(diagnostic, action);
      diagnostics.push(diagnostic);

      console.log("sum + day");
    }

    // Check for else.
    line = document.lineAt(11).text;
    if (line.includes("else")) {
      const diagnostic = {
        code: "",
        message: "Found: else\nExpected: elif",
        range: new vscode.Range(
          new vscode.Position(11, 4),
          new vscode.Position(11, 8)
        ),
        severity: vscode.DiagnosticSeverity.Error,
        source: "PyEdu 🚀",
      };

      const action = new vscode.CodeAction(
        "Replace 'else' with 'elif'",
        vscode.CodeActionKind.QuickFix
      );
      action.edit = new vscode.WorkspaceEdit();
      action.edit.replace(
        document.uri,
        new vscode.Range(
          new vscode.Position(11, 4),
          new vscode.Position(11, 8)
        ),
        "elif"
      );

      action.diagnostics = [diagnostic];

      this.codeActions.set(diagnostic, action);
      diagnostics.push(diagnostic);
      console.log("else");
    }

    // Check for missing comma in print.
    line = document.lineAt(15).text;
    if (line.includes('print("Average:" avg)')) {
      const diagnostic = {
        code: "",
        message: "Found: [space]\nExpected: ,",
        range: new vscode.Range(
          new vscode.Position(15, 16),
          new vscode.Position(15, 17)
        ),
        severity: vscode.DiagnosticSeverity.Error,
        source: "PyEdu 🚀",
      };

      const action = new vscode.CodeAction(
        "Insert ','",
        vscode.CodeActionKind.QuickFix
      );
      action.edit = new vscode.WorkspaceEdit();
      action.edit.replace(
        document.uri,
        new vscode.Range(
          new vscode.Position(15, 16),
          new vscode.Position(15, 17)
        ),
        ", "
      );

      action.diagnostics = [diagnostic];

      this.codeActions.set(diagnostic, action);
      diagnostics.push(diagnostic);
      console.log("print");
    }

    this.diagnosticCollection.set(document.uri, diagnostics);
  }

  public update(document: vscode.TextDocument, fixes: pymacer.Fixes) {
    if (document && path.basename(document.uri.fsPath) === "rainfall.py") {
      if (this.feedbackLevel === FeedbackLevel.novice) {
        this.updateForNovices(document);
      } else {
        this.updateForExperts(document);
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
