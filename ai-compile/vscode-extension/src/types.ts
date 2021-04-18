export interface Payload {
    source: string;
    lastEditLine: number;
}

export interface Response {
    lineNo: number;
    lineText: string;
}

export interface DocumentStore {
    filePath: string,   // placeholder for additional fields
    fixes: Fix    
}

export type Fix = ( Response[] | undefined );
