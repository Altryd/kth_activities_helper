'use client'
import { useState } from 'react';

export default function SubscribePage() {
    const handleSubscribe = async () => {
        try {
            const response = await fetch("http://localhost:8089/api/subscribe", {
                credentials: "include",
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    user_id: "discordID", 
                }),
            });

            if (response.ok) {
                alert("Subscribed successfully!");
            } else {
                alert("Failed to subscribe");
            }
        } catch (error) {
            console.error("Error occurred during subscription:", error);
            alert("Error occurred during subscription");
        }
    };

    return (
        <div className="flex justify-center items-center h-screen">
            <button onClick={handleSubscribe} className="px-6 py-3 bg-blue-500 text-white rounded-lg">
                SUBSCRIBE
            </button>
        </div>
    );
}
