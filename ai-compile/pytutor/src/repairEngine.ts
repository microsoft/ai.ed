import { Modes } from "./util";

/*
    Defines an interface for the repair engine and list of suppoerted engines. 
    Currently, only pymacer is supported.
*/
export const PYMACER = 1;

export enum RepairEngineTypes {
	PyMacer = PYMACER,
}

export interface RepairEngine{
	populateCodeActions(): Map<import("vscode").Diagnostic, import("vscode").CodeAction>;
    process(mode: Modes):Promise<boolean>;	
}