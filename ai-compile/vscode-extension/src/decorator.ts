import * as vscode from "vscode";

import { documentStore } from "./extension";
import * as pymacer from "./pymacer";

export class Decorator {
  
  private decorationType: vscode.TextEditorDecorationType;
  private insertDecorationType: vscode.TextEditorDecorationType;
  private deleteDecorationType: vscode.TextEditorDecorationType;
  private replaceDecorationType: vscode.TextEditorDecorationType;
  private eventDisposables: vscode.Disposable[] = [];
  private regEx;

  constructor() {
    // create a decorator type used for generic decorations
    this.decorationType = vscode.window.createTextEditorDecorationType({
      borderWidth: "1px",
      borderStyle: "solid",
      overviewRulerColor: "blue",
      overviewRulerLane: vscode.OverviewRulerLane.Right,
      light: {
        // this color will be used in light color themes
        borderColor: "darkblue",
        backgroundColor: "lightblue",
      },
      dark: {
        // this color will be used in dark color themes
        borderColor: "lightblue",
        backgroundColor: "darkblue",
      },
    });

    // create a decorator type that we use to decorate insert operations
    this.insertDecorationType = vscode.window.createTextEditorDecorationType({
      borderWidth: "1px",
      borderStyle: "solid",
      overviewRulerColor: "green",
      overviewRulerLane: vscode.OverviewRulerLane.Right,
      light: {
        // this color will be used in light color themes
        borderColor: "darkgreen",
        backgroundColor: "lightgreen",
      },
      dark: {
        // this color will be used in dark color themes
        borderColor: "lightgreen",
        backgroundColor: "darkgreen",
      },
    });

    // create a decorator type that we use to decorate delete operations
    this.deleteDecorationType = vscode.window.createTextEditorDecorationType({
      borderWidth: "1px",
      borderStyle: "solid",
      overviewRulerColor: "red",
      overviewRulerLane: vscode.OverviewRulerLane.Right,
      light: {
        // this color will be used in light color themes
        borderColor: "darkred",
        backgroundColor: "lightred",
      },
      dark: {
        // this color will be used in dark color themes
        borderColor: "lightred",
        backgroundColor: "darkred",
      },
    });

    // create a decorator type that we use to decorate replace
    this.replaceDecorationType = vscode.window.createTextEditorDecorationType({
      borderWidth: "1px",
      borderStyle: "solid",
      overviewRulerColor: "blue",
      overviewRulerLane: vscode.OverviewRulerLane.Right,
      light: {
        // this color will be used in light color themes
        borderColor: "darkblue",
        backgroundColor: "lightblue",
      },
      dark: {
        // this color will be used in dark color themes
        borderColor: "lightblue",
        backgroundColor: "darkblue",
      },
    });

    this.regEx = /(.+)/g;
  }

  public updateDecorations() {
    const activeEditor = vscode.window.activeTextEditor;
    if (!activeEditor) {
      return;
    }

    const document = activeEditor.document;
    const filePath = document.uri.fsPath;
    const highlights: vscode.DecorationOptions[] = [];
    const insertHighlights: vscode.DecorationOptions[] = [];
    const deleteHighlights: vscode.DecorationOptions[] = [];
    const replaceHighlights: vscode.DecorationOptions[] = [];

    // an indicator to choosing a particular feedback level 
    const activeHighlight: number = vscode.workspace
      .getConfiguration("python-hints")
      .get("activeHighlight", 0);
    
    if (activeHighlight !== 0) {

      const fixes: pymacer.Fixes = documentStore.get(filePath)?.fixes;
      fixes?.forEach((fix) => {
        const position = new vscode.Position(fix.lineNo, 0);
        let range = document.getWordRangeAtPosition(
          position,
          new RegExp(this.regEx)
        );

        let diagnosticMsg: string = "";

        switch (activeHighlight) {
          case 1: {
            diagnosticMsg = fix.feedback[0].fullText;
            break;
          }
          case 2: {
            diagnosticMsg = fix.editDiffs[0].type.toUpperCase();
            break;
          }
        }

        const decoration = { range: range!, hoverMessage: diagnosticMsg };
        highlights.push(decoration);

        fix.editDiffs?.forEach((edit) => {
          const startPos = new vscode.Position(fix.lineNo, edit.start);
          const endPos = new vscode.Position(fix.lineNo, edit.end + 1);
          const range = new vscode.Range(startPos, endPos);
          if (edit.type === "insert") {
            const insertDecoration = {
              range: range,
              hoverMessage: diagnosticMsg,
            };
            insertHighlights.push(insertDecoration);
          } else if (edit.type === "delete") {
            const deleteDecoration = {
              range: range,
              hoverMessage: diagnosticMsg,
            };
            deleteHighlights.push(deleteDecoration);
          } else {
            const replaceDecoration = {
              range: range,
              hoverMessage: diagnosticMsg,
            };
            replaceHighlights.push(replaceDecoration);
          }
        });
      });
    }

    if (activeHighlight < 2) {
      activeEditor.setDecorations(this.decorationType, highlights);
      activeEditor.setDecorations(this.insertDecorationType, []);
      activeEditor.setDecorations(this.deleteDecorationType, []);
      activeEditor.setDecorations(this.replaceDecorationType, []);
    } else {
      activeEditor.setDecorations(this.decorationType, []);
      activeEditor.setDecorations(this.insertDecorationType, insertHighlights);
      activeEditor.setDecorations(this.deleteDecorationType, deleteHighlights);
      activeEditor.setDecorations(
        this.replaceDecorationType,
        replaceHighlights
      );
    }
  }

  // this method is called in the extension activation function
  public registerDecorator(
    context: vscode.ExtensionContext
  ) {

    this.eventDisposables.push(
      vscode.window.onDidChangeActiveTextEditor(
        (editor) => {
          if (editor) {
            this.updateDecorations();
          }
        },
        null,
        context.subscriptions
      )
    );

    this.eventDisposables.push(
      vscode.workspace.onDidChangeTextDocument(
        (event) => {
          const activeEditor = vscode.window.activeTextEditor;
          if (activeEditor && event.document === activeEditor.document) {
            this.updateDecorations();
          }
        },
        null,
        context.subscriptions
      )
    );
  }
}
