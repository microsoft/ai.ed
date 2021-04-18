import * as vscode from 'vscode';
import { promisify } from 'util';
import { exec } from 'child_process';

import axios from 'axios';
import * as https from 'https';

import { requestTimeOut, shellCmdTimeOut } from './constants';
import * as t from "./types";

export class Document implements t.DocumentStore {
    private _filePath: string;
    private _fixes: t.Fix;

    constructor(
        filePath: string,
        fixes: t.Fix
    ) {
        this._filePath = filePath;
        this._fixes = fixes;
    }

    public get fixes() {
        return this._fixes;
    }
    public set fixes( value: t.Fix ) {
        this._fixes = value;
    }

    public get filePath() {
        return this._filePath;
    }
    public set filePath( value: string ) {
        this._filePath = value;
    }
    
}


export class LocalStorage {
    
    constructor( private storage: vscode.Memento ) { }

    public getValue<T>( key: string ): ( T | undefined ) {
        return this.storage.get<T>( key );
    }

    public setValue<T>( key: string, value: T ) {
        this.storage.update( key, value );
    }
}


export async function compile (
    filePath: string
): Promise<boolean> {
    const command = `python -m py_compile "${filePath}"`;
    const options = {
        windowsHide: true,
        timeout: shellCmdTimeOut
    };
    try {
        const execute = promisify(exec);
        const { stdout, stderr } = await execute( command, options );
        if( stderr ) {
            return false;
        }
        return true;
    }
    catch( exception ) {
        return false;
    }
}


export async function getFix (
    baseURL: string,
    data: t.Payload
): Promise<t.Fix> {
    const agent = new https.Agent({  
        rejectUnauthorized: false
    });
    try {
        const response = await axios.post(baseURL, data, { timeout: requestTimeOut, httpsAgent: agent });
        return response.data as t.Fix;
    } catch (error) {
        return undefined;
    }
}
