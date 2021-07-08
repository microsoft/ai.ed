import * as vscode from "vscode";
import * as path from "path";

export const alphaNumRegExp = /[a-z0-9_]+/ig;

export const nonWhiteSpaceRegExp = /[^\s]+/ig;

export function isAlphaNum (charCode: number): boolean
{
    return !(!(charCode > 47 && charCode < 58) && // (0-9)
    !(charCode > 64 && charCode < 91) && // (A-Z)
    !(charCode > 96 && charCode < 123)); // (a-z)
};

export function isPythonFile (document: vscode.TextDocument): boolean
{
    const filePathNameInParts = path.basename(document.uri.fsPath).split('.');
    const fileExtension = filePathNameInParts[filePathNameInParts.length-1];
    return fileExtension === "py";
}

// standard interface for code action diagnostic in VS Code
export interface Diagnostic {
    code: string;
    message: string;
    range: vscode.Range;
    severity: vscode.DiagnosticSeverity;
    source: string;
}