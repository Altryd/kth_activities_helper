"use client";
import React, { useState } from 'react';
import 'tailwindcss/tailwind.css';
// discordId uint64, rating uint32, username string, active bool
type User = {
    osu_id: number,
    discord_id: string,
    rating: number, 
    username: string,
    active: boolean,
    MatchUserScrim: Array<object>
};

const API_URL_GET_USERS = "http://localhost:8089/api/users";

export default function UsersPage() {
    const [users, setUsers] = React.useState<User[]>([]);
    const [selectedUser, setSelectedUser] = useState<User | null>(null);
    const [isModalOpen, setIsModalOpen] = useState(false);

    React.useEffect(() => {
        fetch(API_URL_GET_USERS, { credentials: "include" })
            .then(response => response.json())
            .then(data => setUsers(data.users));
    }, []);

    const openModal = (user: User) => {
        setSelectedUser(user);
        setIsModalOpen(true);
    };

    const handleInputChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
        const { name, value } = e.target;
        if (selectedUser) {
            setSelectedUser({ ...selectedUser, [name]: value });
        }
    };
    function transformUser(user: User) {
        return {
            // osu_id: user.osu_id,
            discord_id: String(user.discord_id),
            rating: Number(user.rating),
            username: user.username,
            active: Boolean(Number(user.active)),
        };
      }
      const handleSubmit = async () => {
        if (selectedUser) {
          try {
            const transformedUser = transformUser(selectedUser); // Проверьте правильность работы этой функции
            
            const response = await fetch(
              `http://localhost:8089/api/user/${selectedUser.osu_id}/edit`, 
              {
                method: "PUT",
                headers: {
                  "Content-Type": "application/json",
                },
                body: JSON.stringify(transformedUser),
              }
            );
      
            if (!response.ok) {
              const errorData = await response.json();
              console.error("Server error:", errorData);
              throw new Error(`Request failed with status ${response.status}`);
            }
      
            console.log("User updated successfully");
            setUsers((prevUsers) =>
                prevUsers.map((user) =>
                    user.osu_id === selectedUser.osu_id
                        ? { ...user, ...transformedUser }
                        : user
                )
            );

          } catch (error) {
            console.error(`Edit user ERROR: ${error}`);
          } finally {

            setIsModalOpen(false);
          }
        }
      };
    return (
        <div className="grid grid-cols-4 gap-4 p-4">
            {users.map((user) => (
                <div
                    key={user.osu_id}
                    className="flex items-center justify-between p-4 bg-white shadow rounded-lg cursor-pointer"
                    onClick={() => openModal(user)}
                >
                    <div className="flex flex-col space-y-1">
                        <h2 className="text-lg font-semibold">{user.username}</h2>
                        <p className="text-sm">Rating: {user.rating}</p>
                    </div>
                    <div className="flex flex-col space-y-2 items-end">
                        <div className="text-md">Discord Id: {user.discord_id}</div>
                        <div className="text-md">Osu Id: {user.osu_id}</div>
                        <div className="text-md">
                            {user.active ? "Active" : "Inactive"}
                        </div>
                    </div>
                </div>
            ))}
            {isModalOpen && selectedUser && (
                <div className="fixed inset-0 flex items-center justify-center bg-black bg-opacity-50">
                    <div className="bg-white p-8 rounded-lg w-96">
                        <h2 className="text-xl font-bold mb-4">Edit User</h2>
                        <form onSubmit={(e) => e.preventDefault()}>
                            <label className="block mb-2">Username</label>
                            <input
                                type="text"
                                name="username"
                                value={selectedUser.username}
                                onChange={handleInputChange}
                                className="w-full p-2 mb-4 border rounded"
                            />

                            <label className="block mb-2">Rating</label>
                            <input
                                type="number"
                                name="rating"
                                value={selectedUser.rating}
                                onChange={handleInputChange}
                                className="w-full p-2 mb-4 border rounded"
                            />

                            <label className="block mb-2">Discord Id</label>
                            <input
                                type="text"
                                name="discord_id"
                                value={selectedUser.discord_id}
                                onChange={handleInputChange}
                                className="w-full p-2 mb-4 border rounded"
                            />

                            <label className="block mb-2">Active</label>
                            <select
                                name="active"
                                value={Boolean(Number(selectedUser.active)) ? 1 : 0}
                                onChange={handleInputChange}
                                className="w-full p-2 mb-4 border rounded"
                            >
                                <option value={1}>Active</option>
                                <option value={0}>Inactive</option>
                            </select>

                            <div className="flex justify-end space-x-4">
                                <button
                                    type="button"
                                    className="px-4 py-2 bg-gray-400 text-white rounded"
                                    onClick={() => setIsModalOpen(false)}
                                >
                                    Cancel
                                </button>
                                <button
                                    type="button"
                                    className="px-4 py-2 bg-blue-600 text-white rounded"
                                    onClick={handleSubmit}
                                >
                                    Save
                                </button>
                            </div>
                        </form>
                    </div>
                </div>
            )}
        </div>
    );
}
