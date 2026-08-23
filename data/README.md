# Data fixtures

`demo/` contains candidate fixtures: the synthetic Minh Tran profile and a privacy-minimised, user-provided Phung Dang Khoa profile used only for the reviewed demo PDF. Direct contact details and date of birth are deliberately excluded. It also contains upload-ready synthetic JDs with reproducible generators. `reference/` contains provisional target-role, mapping, and JD-skill JSON used by deterministic demo mode. These files are not externally validated evidence; replace them through the sourced, human-reviewed build process in `Docs/ARCHITECTURE.md` before enabling live AI or making evaluation claims.

Regenerate the CV with the bundled Python environment or any Python installation containing `python-docx`:

```bash
python data/demo/generate_demo_cv.py
```

The first ten operations JD files live in `data/demo/jds/`; `data/demo/jds/tech/` adds ten Data/Engineering/Cloud/Security/ML/QA roles plus the Product Owner JD used in the Khoa demo video. ZIP packages under `data/demo/` make the original two sets easy to transfer to another test machine.
