let currentPage = 1;
const limit = 24; 
let currentQuery = '';

const container = document.getElementById('devicesContainer');
const searchInput = document.getElementById('searchInput');
const prevBtn = document.getElementById('prevBtn');
const nextBtn = document.getElementById('nextBtn');
const pageInfo = document.getElementById('pageInfo');
const stats = document.getElementById('stats');

// The data is now available locally from window.DEVICES_DATA (bypassing backend)
const allDevices = window.DEVICES_DATA || [];

/**
 * Escapes HTML characters in metadata strings to prevent injection when rendering DOM template.
 * @param {string} str - Raw input string.
 * @returns {string} HTML safe string.
 */
function escapeHtml(str) {
    if (!str) return '';
    return String(str)
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;');
}

/**
 * Filters and paginates devices based on current query and page state.
 */
function fetchDevices() {
    // Client-side search & filtering
    let filtered = allDevices;
    if (currentQuery) {
        const q = currentQuery.toLowerCase();
        filtered = allDevices.filter(d => 
            (d.Name && d.Name.toLowerCase().includes(q)) || 
            (d.Model && d.Model.toLowerCase().includes(q)) ||
            (d.Version && d.Version.toLowerCase().includes(q))
        );
    }

    // Client-side pagination
    const total = filtered.length;
    const totalPages = Math.ceil(total / limit) || 1;
    
    // Ensure current page is valid after a search
    if (currentPage > totalPages) currentPage = totalPages;
    if (currentPage < 1) currentPage = 1;

    const startIndex = (currentPage - 1) * limit;
    const endIndex = currentPage * limit;
    const paginatedItems = filtered.slice(startIndex, endIndex);

    renderDevices(paginatedItems);
    updatePagination(total, totalPages);
}

/**
 * Renders the device cards into the container element.
 * @param {Array<Object>} devices - List of device objects to display for the current page.
 */
function renderDevices(devices) {
    if (!devices || devices.length === 0) {
        container.innerHTML = '<div class="col-span-full text-center py-10 text-gray-500">No devices found.</div>';
        return;
    }

    container.innerHTML = devices.map(d => {
        const name = escapeHtml(d.Name || 'Unknown Device');
        const model = escapeHtml(d.Model || 'N/A');
        const version = escapeHtml(d.Version || 'N/A');

        // Construct full URL for local images relative to index.html
        // d.Image_URL is like "/images/filename.svg"
        let imgUrl = d.Image_URL ? '..' + d.Image_URL : 'https://via.placeholder.com/100?text=No+Image';
            
        return `
        <div class="bg-white rounded-xl shadow-sm border border-gray-100 p-5 flex flex-row sm:flex-col items-center sm:items-start gap-4 hover:shadow-md transition">
            <div class="flex-shrink-0 sm:w-full flex justify-center">
                <img src="${imgUrl}" alt="${name}" class="w-16 h-16 sm:w-24 sm:h-24 object-contain">
            </div>
            <div class="flex-1 min-w-0">
                <h2 class="text-lg font-bold text-gray-900 truncate" title="${name}">${name}</h2>
                <p class="text-sm text-gray-500 mt-1"><strong>Model:</strong> ${model}</p>
                <p class="text-sm text-gray-500"><strong>OS:</strong> ${version}</p>
            </div>
        </div>
        `;
    }).join('');
}

/**
 * Updates pagination state text and button disabled attributes.
 * @param {number} total - Total count of matched devices.
 * @param {number} totalPages - Total calculated pages.
 */
function updatePagination(total, totalPages) {
    pageInfo.innerText = `Page ${currentPage} of ${totalPages}`;
    stats.innerText = `${total.toLocaleString()} devices found`;

    prevBtn.disabled = currentPage <= 1;
    nextBtn.disabled = currentPage >= totalPages;
}

// Event Listeners
searchInput.addEventListener('input', (e) => {
    currentQuery = e.target.value.trim();
    currentPage = 1; 
    fetchDevices();
});

prevBtn.addEventListener('click', () => {
    if (currentPage > 1) {
        currentPage--;
        fetchDevices();
        window.scrollTo({ top: 0, behavior: 'smooth' });
    }
});

nextBtn.addEventListener('click', () => {
    currentPage++;
    fetchDevices();
    window.scrollTo({ top: 0, behavior: 'smooth' });
});

// Initial load
fetchDevices();