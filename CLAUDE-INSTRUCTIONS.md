# Portfolio Setup for Claude

When I ask Claude to help with a new project, use this structure:

## My Portfolio Location
`~/Desktop/alex-bespalov-portfolio/`

## Required Files for Each Project
- README.md (professional, with problem/solution/impact)
- requirements.txt (Python dependencies)
- .gitignore (copy from ai-stock-analyzer)
- LICENSE (MIT - copy from ai-stock-analyzer)
- assets/ folder with screenshots
- My code files

## README Template
Use similar format to ai-stock-analyzer/README.md:
- Badges at top
- Overview with problem/solution/impact
- Tech stack
- Setup instructions
- Results/metrics
- License and contact

## Folder Naming
- Use kebab-case: `customer-analytics`, `data-pipeline`
- Be descriptive, not generic

## Git Workflow
```bash
cd ~/Desktop/alex-bespalov-portfolio
git add project-name/
git commit -m "feat: Add [description]"
git push origin main
```

## What NOT to Push
- Secrets/API keys (use .gitignore)
- Large data files
- Template folders (keep those local)
- WIP or incomplete projects

---

That's it! Keep it simple and professional.
