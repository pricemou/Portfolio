import fs from "fs";
import path from "path";
import { fileURLToPath } from "url";
const __dirname = path.dirname(fileURLToPath(import.meta.url));
const root = path.join(__dirname, "..");
console.log("CV files in public/cv:", fs.readdirSync(path.join(root, "public", "cv")));
console.log("Open the .html files in a browser and Print → Save as PDF for a 1-page PDF.");
