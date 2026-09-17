const express = require('express');
const fs = require('fs');
const cors = require('cors');
const path = require('path');

const app = express();
app.use(cors());

// STATIC ROUTE FOR IMAGES: Serves the downloaded images
app.use('/images', express.static(path.join(__dirname, '../images')));

let devices = [];

// Load data directly from the newly created JSON file instead of CSV
const jsonPath = path.join(__dirname, '../data/devices.json');
if (fs.existsSync(jsonPath)) {
    try {
        devices = JSON.parse(fs.readFileSync(jsonPath, 'utf8'));
        console.log(`Loaded ${devices.length} devices from JSON.`);
    } catch (err) {
        console.error("Error parsing devices.json:", err);
    }
} else {
    console.warn("devices.json not found! Please run export_data.py first.");
}

app.get('/api/devices', (req, res) => {
    let page = parseInt(req.query.page) || 1;
    let limit = parseInt(req.query.limit) || 20;
    let startIndex = (page - 1) * limit;
    let endIndex = page * limit;
    
    res.json({
        total: devices.length,
        page,
        limit,
        data: devices.slice(startIndex, endIndex)
    });
});

app.get('/api/devices/search', (req, res) => {
    let q = (req.query.q || '').toLowerCase();
    let page = parseInt(req.query.page) || 1;
    let limit = parseInt(req.query.limit) || 20;
    
    let filtered = devices;
    if (q) {
        filtered = devices.filter(d => 
            (d.Name && d.Name.toLowerCase().includes(q)) || 
            (d.Model && d.Model.toLowerCase().includes(q)) ||
            (d.Version && d.Version.toLowerCase().includes(q))
        );
    }
    
    let startIndex = (page - 1) * limit;
    let endIndex = page * limit;
    
    res.json({
        total: filtered.length,
        page,
        limit,
        data: filtered.slice(startIndex, endIndex)
    });
});

const PORT = process.env.PORT || 3000;
app.listen(PORT, () => {
    console.log(`API Server running on http://localhost:${PORT}`);
    console.log(`Image Server running on http://localhost:${PORT}/images/`);
});
