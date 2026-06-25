const fs = require('fs');
const js = fs.readFileSync('D:/tooling-management/backend/_check_syntax.js', 'utf-8');
try {
    new Function(js);
    console.log('SYNTAX OK - no errors');
} catch(e) {
    console.log('SYNTAX ERROR: ' + e.message);
    console.log('Line: ' + e.lineNumber + ' Col: ' + e.columnNumber);
    const lines = js.split('\n');
    const errLine = e.lineNumber - 1;
    for (let i = Math.max(0, errLine-3); i < Math.min(lines.length, errLine+3); i++) {
        console.log((i+1) + ': ' + lines[i]);
    }
}
