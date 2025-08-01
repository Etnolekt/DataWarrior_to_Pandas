#!/usr/bin/env node
import OCL from './node_modules/openchemlib/dist/openchemlib.js';

function decodeIdcode(idcode) {
    if (!idcode) {
        throw new Error("IDCode cannot be empty");
    }
    
    try {
        const molecule = OCL.Molecule.fromIDCode(idcode);
        if (!molecule) {
            throw new Error("Failed to create molecule from IDCode");
        }
        const smiles = molecule.toSmiles();
        if (!smiles) {
            throw new Error("Failed to generate SMILES");
        }
        return smiles;
    } catch (e) {
        throw new Error(`Failed to decode: ${e.message}`);
    }
}

// Handle command line usage
if (import.meta.url === `file://${process.argv[1]}`) {
    const args = process.argv.slice(2);
    
    if (args.length === 0) {
        console.error("Please provide ID codes as arguments");
        console.error("Usage: node decode.mjs <idcode1> [idcode2] [idcode3] ...");
        process.exit(1);
    }
    
    // Process all ID codes provided as arguments
    for (let i = 0; i < args.length; i++) {
        const idcode = args[i];
        try {
            const smiles = decodeIdcode(idcode);
            console.log(`${i}:${smiles}`);
        } catch (error) {
            console.log(`${i}:ERROR:${error.message}`);
        }
    }
}

// Export for use as module
export { decodeIdcode }; 