import { useEffect, useState } from 'react';
import './index.css';

function formatDate(value) {
    if (!value) {
        return 'Not sent';
    }

    const date = new Date(value);
    if (Number.isNaN(date.getTime())) {
        return 'Not sent';
    }

    return date.toLocaleString();
}

function App() {
    const [campaigns, setCampaigns] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState('');
    const [selectedCampaignId, setSelectedCampaignId] = useState(null);
    const [selectedCampaign, setSelectedCampaign] = useState(null);
    const [detailLoading, setDetailLoading] = useState(false);
    const [detailError, setDetailError] = useState('');

    useEffect(() => {
        const loadCampaigns = async () => {
            try {
                const response = await fetch('/campaigns');
                if (!response.ok) {
                    throw new Error('Failed to load campaigns');
                }

                const data = await response.json();
                setCampaigns(data);
            } catch (err) {
                setError(err.message || 'Something went wrong');
            } finally {
                setLoading(false);
            }
        };

        loadCampaigns();
    }, []);

    useEffect(() => {
        if (!selectedCampaignId) {
            return;
        }

        let isActive = true;
        const loadCampaign = async () => {
            setDetailLoading(true);
            setDetailError('');

            try {
                const response = await fetch(`/campaigns/${selectedCampaignId}`);
                if (!response.ok) {
                    throw new Error('Failed to load campaign details');
                }

                const data = await response.json();
                if (isActive) {
                    setSelectedCampaign(data);
                }
            } catch (err) {
                if (isActive) {
                    setDetailError(err.message || 'Something went wrong');
                    setSelectedCampaign(null);
                }
            } finally {
                if (isActive) {
                    setDetailLoading(false);
                }
            }
        };

        loadCampaign();

        return () => {
            isActive = false;
        };
    }, [selectedCampaignId]);

    return (
        <div className="app-shell">
            <header className="top-bar">
                <h1>Email Campaigns</h1>
                <button className="primary-btn" type="button">
                    Create campaign
                </button>
            </header>

            {!selectedCampaignId ? (
                <section className="campaign-list">
                    <p className="section-label">Your campaigns</p>
                    {loading && <p className="status-text">Loading campaigns...</p>}
                    {error && <p className="status-text error">{error}</p>}
                    {!loading && !error && campaigns.length === 0 && (
                        <p className="status-text">No campaigns found yet.</p>
                    )}
                    {!loading && !error && campaigns.map((campaign) => (
                        <button
                            key={campaign.id}
                            type="button"
                            className="campaign-card"
                            onClick={() => setSelectedCampaignId(campaign.id)}
                        >
                            <span className="campaign-title">{campaign.title}</span>
                            <span className="campaign-meta">{campaign.emails} emails</span>
                        </button>
                    ))}
                </section>
            ) : (
                <section className="campaign-detail">
                    <button
                        className="secondary-btn"
                        type="button"
                        onClick={() => setSelectedCampaignId(null)}
                    >
                        Back to campaigns
                    </button>

                    {detailLoading && <p className="status-text">Loading campaign details...</p>}
                    {detailError && <p className="status-text error">{detailError}</p>}

                    {!detailLoading && !detailError && selectedCampaign && (
                        <>
                            <h2>{selectedCampaign.name || selectedCampaign.title}</h2>
                            <div className="detail-section">
                                <h3>Subject</h3>
                                <p>{selectedCampaign.subject || 'No subject provided.'}</p>
                            </div>
                            <div className="detail-section">
                                <h3>Body</h3>
                                <p>{selectedCampaign.body || 'No body provided.'}</p>
                            </div>
                            <div className="detail-section">
                                <h3>Emails</h3>
                                {(selectedCampaign.emails || []).length === 0 ? (
                                    <p>No emails added yet.</p>
                                ) : (
                                    <div className="email-list">
                                        {(selectedCampaign.emails || []).map((email, index) => (
                                            <div key={email.id || `${email.address}-${index}`} className="email-row">
                                                <span className="email-address">{email.address || `Email ${index + 1}`}</span>
                                                <span className="email-status">{email.status || 'pending'}</span>
                                                <span className="email-date">{formatDate(email.sent_at)}</span>
                                            </div>
                                        ))}
                                    </div>
                                )}
                            </div>
                        </>
                    )}
                </section>
            )}
        </div>
    );
}

export default App;
