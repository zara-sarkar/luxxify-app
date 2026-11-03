import React, { useState } from 'react';
import './index.css';

const skinToneOptions = {
  Light: '/images/fair_skin.jpg',
  Medium: '/images/tan_skin.jpg',
  Deep: '/images/dark_skin.jpg',
};

const conditionOptions = {
  Wrinkles: '/images/wrinkles.jpg',
  Acne: '/images/acne.jpg',
  Hyperpigmentation: '/images/hyperpigmentation.jpg',
  'Dark Circles': '/images/dark_circles.jpg',
  'Redness/Rosacea': '/images/redness.jpg',
  'Sensitive Skin': '/images/sensitive.jpg',
};

export default function App() {
  const [formData, setFormData] = useState({
    age_range: '20-30',
    skin_type: 'Oily',
    experience_level: 'Beginner',
    coverage: 'Medium',
    max_budget: 20,
    selected_skin_tone: 'Light',
    conditions: {},
    lifestyle_options: [],
    active_options: '2 - Moderately Busy/Active',
  });

  const [results, setResults] = useState([]);
  const [loading, setLoading] = useState(false);

  const handleConditionToggle = (condition) => {
    setFormData((prev) => ({
      ...prev,
      conditions: {
        ...prev.conditions,
        [condition]: !prev.conditions[condition],
      },
    }));
  };

  const handleLifestyleToggle = (option) => {
    setFormData((prev) => {
      const exists = prev.lifestyle_options.includes(option);
      return {
        ...prev,
        lifestyle_options: exists
          ? prev.lifestyle_options.filter((item) => item !== option)
          : [...prev.lifestyle_options, option],
      };
    });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    try {
      const response = await fetch('http://localhost:8000/api/recommendations', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(formData),
      });
      const data = await response.json();
      setResults(data);
    } catch (err) {
      console.error('Error fetching recommendations:', err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="container">
      <h1>Makeup Recommendations</h1>

      <form onSubmit={handleSubmit}>
        <div className="form-group">
          <label>Select Age Range</label>
          <select
            value={formData.age_range}
            onChange={(e) => setFormData({ ...formData, age_range: e.target.value })}
          >
            {['Under 20', '20-30', '30-40', '40-50', '50+'].map((val) => (
              <option key={val} value={val}>{val}</option>
            ))}
          </select>
        </div>

        <div className="form-group">
          <label>Select Skin Type</label>
          <select
            value={formData.skin_type}
            onChange={(e) => setFormData({ ...formData, skin_type: e.target.value })}
          >
            {['Oily', 'Dry', 'Combination'].map((val) => (
              <option key={val} value={val}>{val}</option>
            ))}
          </select>
        </div>

        <div className="form-group">
          <label>Experience Level</label>
          <select
            value={formData.experience_level}
            onChange={(e) => setFormData({ ...formData, experience_level: e.target.value })}
          >
            {['Beginner', 'Intermediate', 'Pro'].map((val) => (
              <option key={val} value={val}>{val}</option>
            ))}
          </select>
        </div>

        <div className="form-group">
          <label>Coverage</label>
          <select
            value={formData.coverage}
            onChange={(e) => setFormData({ ...formData, coverage: e.target.value })}
          >
            {['Light', 'Medium', 'Full'].map((val) => (
              <option key={val} value={val}>{val}</option>
            ))}
          </select>
        </div>

        <div className="form-group">
          <label>Maximum Price Per Product ($)</label>
          <input
            type="number"
            min="0"
            max="1000"
            value={formData.max_budget}
            onChange={(e) => setFormData({ ...formData, max_budget: Number(e.target.value) })}
          />
        </div>

        <h3>Select Skin Tone</h3>
        <div className="grid-3">
          {Object.entries(skinToneOptions).map(([tone, imgPath]) => (
            <div
              key={tone}
              className={`card ${formData.selected_skin_tone === tone ? 'selected' : ''}`}
              onClick={() => setFormData({ ...formData, selected_skin_tone: tone })}
            >
              <img src={imgPath} alt={tone} />
              <p>{tone}</p>
            </div>
          ))}
        </div>

        <h3>Skin Conditions</h3>
        <div className="grid-3">
          {Object.entries(conditionOptions).map(([cond, imgPath]) => (
            <div
              key={cond}
              className={`card ${formData.conditions[cond] ? 'selected' : ''}`}
              onClick={() => handleConditionToggle(cond)}
            >
              <img src={imgPath} alt={cond} />
              <p>{cond}</p>
            </div>
          ))}
        </div>

        <h3>Describe Yourself</h3>
        <label>Occupation (Select Multiple)</label>
        <div className="checkbox-group">
          {['Working Professional', 'Mom/Parent', 'Student', 'Retired'].map((item) => (
            <label key={item}>
              <input
                type="checkbox"
                checked={formData.lifestyle_options.includes(item)}
                onChange={() => handleLifestyleToggle(item)}
              />
              {item}
            </label>
          ))}
        </div>

        <div className="form-group" style={{ marginTop: '15px' }}>
          <label>How Active/Busy Are You?</label>
          <select
            value={formData.active_options}
            onChange={(e) => setFormData({ ...formData, active_options: e.target.value })}
          >
            {['1 - Not Busy/Active', '2 - Moderately Busy/Active', '3 - Super Busy/Active'].map((val) => (
              <option key={val} value={val}>{val}</option>
            ))}
          </select>
        </div>

        <button type="submit" className="submit-btn" disabled={loading}>
          {loading ? 'Finding Best Products...' : 'Get Recommendations'}
        </button>
      </form>

      {results.length > 0 && (
        <div className="results-section">
          <h2>Your Selected Products</h2>
          <table>
            <thead>
              <tr>
                <th>Category</th>
                <th>Product Name</th>
                <th>Price</th>
                <th>Link</th>
              </tr>
            </thead>
            <tbody>
              {results.map((prod, idx) => (
                <tr key={idx}>
                  <td>{prod.category}</td>
                  <td>{prod.product_name}</td>
                  <td>{prod.price}</td>
                  <td>
                    <a href={prod.url} target="_blank" rel="noopener noreferrer">
                      View Product
                    </a>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}