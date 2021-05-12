import * as vscode from "vscode";

export const diagosticCollection = vscode.languages.createDiagnosticCollection(
  "pythonedu"
);

export function updateDiagnostics(document: vscode.TextDocument) {
    
}