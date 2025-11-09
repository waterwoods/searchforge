// Test file for FlowGraph component
import { edgesToMermaid, EdgeData } from './edgesToMermaid';

// Test data
const testEdges: EdgeData[] = [
    { src: "main.py::start", dst: "controller.py::init", type: "calls" },
    { src: "controller.py::init", dst: "config.py::load_settings", type: "calls" },
    { src: "controller.py::init", dst: "database.py::connect", type: "calls" },
    { src: "config.py::load_settings", dst: "settings.py::get_config", type: "calls" },
    { src: "database.py::connect", dst: "models.py::User", type: "imports" },
    { src: "models.py::User", dst: "auth.py::authenticate", type: "calls" },
    { src: "auth.py::authenticate", dst: "utils.py::hash_password", type: "calls" },
    { src: "utils.py::hash_password", dst: "crypto.py::sha256", type: "calls" },
    { src: "models.py::User", dst: "models.py::BaseModel", type: "inherits" },
    { src: "auth.py::authenticate", dst: "auth.py::BaseAuth", type: "inherits" }
];

// Test the function
console.log('Testing edgesToMermaid function...');
const mermaidString = edgesToMermaid(testEdges, { maxNodes: 10 });
console.log('Generated Mermaid string:');
console.log(mermaidString);

// Test empty edges
console.log('\nTesting empty edges...');
const emptyMermaid = edgesToMermaid([]);
console.log('Empty edges result:');
console.log(emptyMermaid);

// Test large graph trimming
console.log('\nTesting large graph trimming...');
const largeEdges = Array.from({ length: 100 }, (_, i) => ({
    src: `file${i}.py::func${i}`,
    dst: `file${i + 1}.py::func${i + 1}`,
    type: 'calls' as const
}));
const trimmedMermaid = edgesToMermaid(largeEdges, { maxNodes: 5 });
console.log('Trimmed graph result:');
console.log(trimmedMermaid);

export { testEdges, mermaidString, emptyMermaid, trimmedMermaid };
