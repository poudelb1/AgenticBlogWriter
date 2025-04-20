document.addEventListener('DOMContentLoaded', () => {
    const blogForm = document.getElementById('blogForm');
    const topicInput = document.getElementById('topicInput');
    const generateButton = document.getElementById('generateButton');
    const buttonText = generateButton.querySelector('.button-text');
    const spinner = generateButton.querySelector('.spinner');
    const loadingIndicator = document.getElementById('loadingIndicator');
    const errorDisplay = document.getElementById('errorDisplay');
    const resultsArea = document.getElementById('resultsArea');
    const blogTitle = document.getElementById('blogTitle');
    const blogImage = document.getElementById('blogImage');
    const blogBody = document.getElementById('blogBody');

    // --- Configuration ---
    // Make sure this URL matches where your FastAPI backend is running
    const API_ENDPOINT = 'http://localhost:8000/api/generate-blog';
    // --------------------

    blogForm.addEventListener('submit', async (event) => {
        event.preventDefault(); // Prevent default form submission

        const topic = topicInput.value.trim();
        if (!topic) {
            showError('Please enter a blog topic.');
            return;
        }

        // --- Start UI Updates ---
        generateButton.disabled = true;
        buttonText.textContent = 'Generating...';
        spinner.style.display = 'inline-block';
        loadingIndicator.style.display = 'block';
        errorDisplay.style.display = 'none';
        resultsArea.style.display = 'none';
        // --- End UI Updates ---

        try {
            const response = await fetch(API_ENDPOINT, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    // Add any other headers if needed (e.g., Authentication)
                },
                body: JSON.stringify({ topic: topic }),
            });

            if (!response.ok) {
                // Try to get error detail from response body
                let errorDetail = `HTTP error! Status: ${response.status}`;
                try {
                    const errorData = await response.json();
                    errorDetail = errorData.detail || errorDetail;
                } catch (parseError) {
                    // Ignore if response body isn't valid JSON
                    console.warn("Could not parse error response body:", parseError);
                }
                 throw new Error(errorDetail);
            }

            const data = await response.json();

            // --- Display Results ---
            blogTitle.textContent = data.title || `Blog on ${topic}`; // Fallback title
            blogImage.src = data.image_url || ''; // Handle potentially missing image URL
            blogImage.alt = `Image for blog post titled: ${data.title || topic}`;
            blogImage.style.display = data.image_url ? 'block' : 'none'; // Hide img tag if no URL

            // Use marked.js to parse Markdown to HTML
            // Ensure marked.js is loaded before this script runs (it is in the HTML)
            // Use marked.parse() (for newer versions) or marked() (older versions)

            if (typeof marked !== 'undefined') {
                    // Prefer parse(), but fallback to the function call if needed
                    const md = data.body_markdown || '';
                    blogBody.innerHTML = marked.parse
                    ? marked.parse(md)
                    : marked(md);
                } else {
                    console.warn("marked.js not loaded; falling back to simple paragraphs");
                    // Naive fallback: split on double newlines into <p> blocks
                    const md = (data.body_markdown || '')
                    .split('\n\n')
                    .map(para => `<p>${para.trim()}</p>`)
                    .join('');
                    blogBody.innerHTML = md;
                }


            resultsArea.style.display = 'block';
            loadingIndicator.style.display = 'none';

        } catch (error) {
            console.error('Error generating blog:', error);
            showError(`Failed to generate blog: ${error.message}`);
            loadingIndicator.style.display = 'none';
        } finally {
            // --- Reset Button ---
            generateButton.disabled = false;
            buttonText.textContent = 'Generate Blog';
            spinner.style.display = 'none';
            // --- End Reset Button ---
        }
    });

    function showError(message) {
        errorDisplay.textContent = message;
        errorDisplay.style.display = 'block';
    }
});