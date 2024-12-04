"use client"
import { userInfo } from "os";
import { useEffect, useState } from "react";
import useSWR from 'swr'

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
    if (error)
    {
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
    return <span>Вы вошли как {data.user.username}, ваш рейтинг: {data.user.rating}</span>
    console.log(data);
    /* useEffect(() => {
    
      const response = fetch("http://localhost:8089/api/me", { 
        credentials: "include",
        method: 'GET',
        headers: {
          'Accept': 'application/json',
        },
    });
    response.then((resp) => {
        resp.json()
        .then((response_json) => {
            console.log(response_json);
            if (response_json['user'].osu_id != user_data.osu_id) {
                setUserData(response_json['user']);
            }
        })
        .catch((err) => {
            
        })
    }).catch((err) => {
        console.log(err);
        // setUserData();
    })
    }) */
    /*useEffect(() => {
        
    })*/
    
    /*if (user_data.osu_id === 0) 
    {   
        const link_to_osu_oauth = "https://osu.ppy.sh/oauth/authorize?client_id=23437&redirect_uri=http%3A%2F%2Flocalhost%3A8089%2Fapi%2Foauth%2Fosu&response_type=code&scope=public+identify&state=randomval";
        return (
            <span>
        <button className="focus:outline-none text-white bg-pink-700 hover:bg-pink-800 focus:ring-4 focus:ring-red-300 font-medium rounded-lg text-sm px-5 py-2.5 me-2 mb-2 dark:bg-red-600 dark:hover:bg-red-700 dark:focus:ring-red-900">
        <a href={link_to_osu_oauth}>
        Войти с помощью osu! аккаунта</a></button></span>
        )
    }
    return <span>Вы вошли как {user_data.username}, ваш рейтинг: {user_data.rating}</span>*/
}