"use client"
import 'tailwindcss/tailwind.css'
import clsx from 'clsx';
import CheckButton from './check_button';
import { useEffect, useState } from 'react';

type playerStruct =  {
	OsuId:     number,
	DiscordId: number,
	Rating:    number,
	Username:  string,
	Active:    boolean,
}

type scrimStruct = {
	PlayerId:     number,
	Player:       playerStruct,
	Score:        number,
	IsBlue:       boolean,
	RatingChange: number,
}

export type matchStruct = {
	Id:     number,
	MatchOsuID:     number,
	MatchTypeId:    number,
	Date:           Date,
	MatchUserScrim: Array<scrimStruct>,
	IsApproved:     boolean,
}

export default function UsersPage() {
    /*
    const AxiosInstance = axios.create({
        baseURL: "http://localhost:8089",
        withCredentials: true
    });
    useEffect(() => {
        AxiosInstance.get("/api/matches")
        .then(() => {
            console.log("udachno");
        })
    }, [])
    */
    const [matches_data, setMatchesData] = useState([]);
    useEffect(() => {
        const response = fetch("http://localhost:8089/api/matches", { 
            credentials: "include",
            method: 'GET',
            headers: {
              'Accept': 'application/json',
            },
        });
        // console.log("ky");
        response.then((resp) => {
            resp.json()
            .then((response_json) => {
                setMatchesData(response_json['matches']);
                // matches_data = response_json['matches'];
                // console.log(matches_data);
            })
            .catch((err) => {
                console.log(err);
                setMatchesData([]);
                // matches_data = [];
            })
        })
        .catch((err) => {
            console.log(err);
            setMatchesData([]);
        })
    }, [])
    
    
    // console.log(matches_data);
    if (matches_data.length == 0) {
        return "Загрузка..";
    }
    // console.log(matches_data);
    return (
        <div className="grid grid-cols-3 gap-4 p-4">
            {matches_data.map((matchstruct: matchStruct) => {
                const date_ = new Date(matchstruct.Date);
                
                // console.log(date_);
                return <div className={clsx(
                    'flex items-center justify-between p-4 shadow rounded-lg',
                    {
                    'bg-gray-100': !matchstruct.IsApproved,
                    'bg-green-100': matchstruct.IsApproved,
                },
                )} key={matchstruct.Id}>
                <div>
                    {date_.getDate()}.{date_.getMonth() + 1}.{date_.getFullYear()} {" | "}
                    {matchstruct.MatchUserScrim[0].Player.Username} {matchstruct.MatchUserScrim[0].Score} {" - "}  
                    {matchstruct.MatchUserScrim[1].Score} {matchstruct.MatchUserScrim[1].Player.Username} <a style={{color: "blue"}} href={"https://osu.ppy.sh/community/matches/" + matchstruct.MatchOsuID}>🌐</a> 
                    <CheckButton matchStruct={matchstruct} text='✓'></CheckButton><button style={{color: "gray"}}>✏️</button><CheckButton matchStruct={matchstruct} text='❌'></CheckButton>
                    
                </div>
            </div>
            })}
        </div>
    );
}