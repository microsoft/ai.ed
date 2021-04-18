import * as vscode from 'vscode';

export const baseURL: string | undefined = vscode.workspace.getConfiguration( "python-hints" ).get( "webServerPath" );

export const requestTimeOut: number = 100000;

export const shellCmdTimeOut: number = 10000;

export const DEBUG: boolean = true;
