import 'tailwindcss/tailwind.css'

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

type matchStruct = {
	Id:     number,
	MatchOsuID:     number,
	MatchTypeId:    number,
	Date:           Date,
	MatchUserScrim: Array<scrimStruct>,
	IsApproved:     boolean,
}

export default async function UsersPage() {
    const response = await fetch("http://localhost:8089/api/matches");
    const resp_json = await response.json();
    const matches_data = resp_json['matches'];
    // console.log(matches_data);
    return (
        <div className="grid grid-cols-1 gap-4 p-4">
            {matches_data.map((matchstruct: matchStruct) => {
                let date_ = new Date(matchstruct.Date);
                // console.log(date_);
                return <div key={matchstruct.Id} className="flex items-center justify-between p-4 bg-white shadow rounded-lg">
                <div>
                    {date_.getDay()}.{date_.getMonth()}.{date_.getFullYear()} {" | "}
                    {matchstruct.MatchUserScrim[0].Player.Username} {matchstruct.MatchUserScrim[0].Score} {" - "}  
                    {matchstruct.MatchUserScrim[1].Score} {matchstruct.MatchUserScrim[1].Player.Username} <i><a style={{color: "blue"}} href={"https://osu.ppy.sh/community/matches/" + matchstruct.MatchOsuID}>Ссылка</a></i>
                </div>
            </div>
            })}
        </div>
    );
}