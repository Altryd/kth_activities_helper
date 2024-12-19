"use client"
import useSWR from 'swr'
import DiscordOauthButton from "./DiscordOAuthButton";

export type UserInfo = {
    osu_id: number,
    discord_id: number,
    rating: number,
    username: string,
    active: boolean,
};

const fetcher = (url: string | URL | Request) => fetch(url, {credentials: "include",
    method: 'GET',
    headers: {
      'Accept': 'application/json',
    },})
    .then(r => r.json())

export default function OsuOAuthButton() {
    // let emptyUserInfo = new UserInfo();
    // const [user_data, setUserData] = useState<UserInfo>({osu_id: 0, discord_id: 0, rating: 0, username: "", active: false});
    // const [isMounted, setIsMounted] = useState(false);

    const { data, error, isLoading } = useSWR('http://localhost:8089/api/me', fetcher)
    console.log(data, error, isLoading);
    let subscription_message = <span>Вы не подписаны на составление пар</span>;
    const link_to_logout = "http://localhost:8089/api/logout";
    let logout_button = <a href={link_to_logout}>
        <button className="focus:outline-none text-white bg-gray-700 hover:bg-gray-800 focus:ring-4 focus:ring-red-300
        font-medium rounded-lg text-sm px-5 py-2.5 me-2 mb-2 dark:bg-red-600 dark:hover:bg-red-700 dark:focus:ring-red-900">
            Выйти из системы</button></a>;
    if (error) {
        const link_to_osu_oauth = "https://osu.ppy.sh/oauth/authorize?client_id=23437&redirect_uri=http%3A%2F%2Flocalhost%3A8089%2Fapi%2Foauth%2Fosu&response_type=code&scope=public+identify&state=randomval";
        return (
            <span>
        <a href={link_to_osu_oauth}><button className="focus:outline-none text-white bg-pink-700 hover:bg-pink-800 focus:ring-4 focus:ring-red-300 font-medium rounded-lg text-sm px-5 py-2.5 me-2 mb-2 dark:bg-red-600 dark:hover:bg-red-700 dark:focus:ring-red-900">
        
        Войти с помощью osu! аккаунта</button></a></span>
        )
    }
    if (isLoading)
    {
        return (
            <span></span>
        )
    }
    if (data.user.active)
    {
        subscription_message = <span><i>Вы подписаны на составление пар</i></span>;
    }
    if (data.user.discord_id == 0)
    {
        return <div>Вы вошли как {data.user.username}, ваш рейтинг: {data.user.rating} 
        <DiscordOauthButton isLoading={isLoading} isLinked={false}/> {subscription_message} {logout_button}
        </div>
    }
    return <div>Вы вошли как {data.user.username}, ваш рейтинг: {data.user.rating}  
    <DiscordOauthButton isLinked={true} isLoading={isLoading}/> {subscription_message}  {logout_button}</div>
}