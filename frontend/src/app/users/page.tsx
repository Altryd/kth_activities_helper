import 'tailwindcss/tailwind.css'

type User = {
    osu_id: number,
    discord_id: number,
    rating: number, 
    username: string,
    active: number,
    MatchUserScrim: Array<object>
};

export default async function UsersPage() {
    // TODO: переделать под клиентский компонент !
    const response = await fetch("http://localhost:8089/api/users", {credentials: "include"});
    const users = await response.json();
    const users_data = users['users'];
    console.log(users_data);
    return (
        <div className="grid grid-cols-4 gap-4 p-4">
            {users_data.map((user: User) => (
                <div key={user.osu_id} className="flex items-center justify-between p-4 bg-white shadow rounded-lg">
                    <div className="flex flex-col space-y-1">
                        <h2 className="text-lg font-semibold">{user.username}</h2>
                        <p className="text-sm">Rating: {user.rating}</p>
                    </div>
                    <div className="flex flex-col space-y-2 items-end">
                        <div className="text-md">Discord Id:{user.discord_id}</div>
                        <div className="text-md">Osu Id: {user.osu_id}</div>
                        <div className="text-md">
                            {user.active && "Active"}
                            {!user.active && "Inactive"}
                        </div>
                    </div>
                </div>
            ))}
        </div>
    );
}