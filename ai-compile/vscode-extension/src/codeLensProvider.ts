import * as vscode from "vscode";
import { docStore } from "./extension";
import * as pymacer from "./pymacer";

export class CodelensProvider implements vscode.CodeLensProvider {
  private codeLenses: vscode.CodeLens[] = [];
  private regex: RegExp;
  private _onDidChangeCodeLenses: vscode.EventEmitter<void> = new vscode.EventEmitter<void>();
  public readonly onDidChangeCodeLenses: vscode.Event<void> = this
    ._onDidChangeCodeLenses.event;

  constructor() {
    // non-empty source lines
    this.regex = /(.+)/g;
    vscode.workspace.onDidChangeConfiguration((_) => {
      this._onDidChangeCodeLenses.fire();
    });
  }

  public provideCodeLenses(
    document: vscode.TextDocument,
    token: vscode.CancellationToken
  ): vscode.CodeLens[] | Thenable<vscode.CodeLens[]> {
    if (
      vscode.workspace
        .getConfiguration("python-hints")
        .get("enableCodeLens", true)
    ) {
      this.codeLenses = [];
      const filePath = document.uri.fsPath;
      const fixes: pymacer.Fix = docStore.get(filePath)?.fixes;
      fixes?.forEach((fix) => {
        const position = new vscode.Position(fix.lineNo, 0);
        const range = document.getWordRangeAtPosition(
          position,
          new RegExp(this.regex)
        );
        var text: string = "";
        if (fix.repairLine[0] === " ") {
          text = "<TAB> ";
        }
        text = text + fix.repairLine;
        let command = {
          command: "python-hints.codelensAction",
          title: text,
        };
        if (range) {
          this.codeLenses.push(new vscode.CodeLens(range, command));
        }
      });
      return this.codeLenses;
    }
    return [];
  }
}
