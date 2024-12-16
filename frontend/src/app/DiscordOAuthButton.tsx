"use client"

export type UserInfo = {
    osu_id: number,
    discord_id: number,
    rating: number,
    username: string,
    active: boolean,
};

/*
const fetcher = (url: string | URL | Request) => fetch(url, {credentials: "include",
    method: 'GET',
    headers: {
      'Accept': 'application/json',
    },})
    .then(r => r.json())*/

export default function DiscordOauthButton(props: {isLinked: boolean, isLoading: boolean}) {
    //const { data, error, isLoading } = useSWR('http://localhost:8089/api/me', fetcher)
    //console.log(data, error, isLoading);
    const link_to_discord_oauth = "https://discord.com/oauth2/authorize?client_id=1311262602604707841&response_type=code&redirect_uri=http%3A%2F%2Flocalhost%3A8089%2Fapi%2Fdiscord&scope=identify+guilds+connections";
    if (props.isLoading)
        {
            return (
                <span></span>
            )
        }
    if (props.isLinked)
        {
            return <span style={{marginLeft: 5}}>Аккаунт дискорда привязан 
                <br/><a href={link_to_discord_oauth}><button className="focus:outline-none text-white bg-blue-700 hover:bg-blue-800 focus:ring-4 focus:ring-red-300 font-medium rounded-lg text-sm px-5 py-2.5 me-2 mb-2 dark:bg-red-600 dark:hover:bg-red-700 dark:focus:ring-red-900">
                    Сменить дискорд аккаунт</button></a>
            </span>
        }
        return (
            <span>
        <a href={link_to_discord_oauth}><button className="focus:outline-none text-white bg-blue-700 hover:bg-blue-800 focus:ring-4 focus:ring-red-300 font-medium rounded-lg text-sm px-5 py-2.5 me-2 mb-2 dark:bg-red-600 dark:hover:bg-red-700 dark:focus:ring-red-900">
        
        Привязать дискорд аккаунт</button></a></span>
        )
   
    // return ""
}