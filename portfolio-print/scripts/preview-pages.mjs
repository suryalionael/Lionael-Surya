// Rasterises every page of the PDF to preview/page-NN.png for visual QA (needs poppler's pdftoppm).
import { execFileSync } from 'node:child_process';
import { mkdirSync } from 'node:fs';
mkdirSync('preview', { recursive: true });
execFileSync('pdftoppm', ['-r', '110', '-png', 'Lionael_Surya_Selected_Projects_2026.pdf', 'preview/page'], { stdio: 'inherit' });
console.log('Wrote preview/page-*.png');
