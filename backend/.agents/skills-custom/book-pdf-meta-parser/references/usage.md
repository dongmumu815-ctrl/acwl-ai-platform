# Usage Guide

## Step 1: Provide PDF URL
When using the agent, provide a valid public PDF URL.

## Step 2: Execution
The tool will:
1. Download the PDF
2. Convert first 5 pages to images
3. Return image paths for model analysis

## Step 3: Model Analysis
Feed the image paths to the model with a prompt like:
```
Extract the following metadata from these PDF page images:
- 正题名
- 副题名
- 作者
- 内容简介
```

## Error Handling
- Invalid URLs will return error messages.
- If PDF has fewer than 5 pages, the tool will notify the user.
- Conversion failures (e.g., password-protected PDFs) are caught and reported.