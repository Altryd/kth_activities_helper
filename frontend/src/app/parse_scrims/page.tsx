'use client'
import { useState } from "react";
import ReactDOM from "react-dom";

export type ParsedLine = {
    id: number,
    match_osu_id: number,
    match_type_id: number,
    date: Date,
    first_player_id: number,
    first_player_username: string,
    first_player_score: number,
    second_player_id: number,
    second_player_username: string,
    second_player_score: number,
};


export default function ParseScrims() {
    let [parsedLines, setParsedLines] = useState([]);
    const SendToDB = async (parsedLine: ParsedLine) => {
        console.log("parsed line: ", parsedLine);
        const response = fetch('http://localhost:8089/api/match', {
            method: 'POST',
            headers: {
              'Accept': 'application/json',
              'Content-Type': 'application/json',
            },
            body: JSON.stringify(
                parsedLine,
            )
          })
        response.then((resp) => {
            let response_json = resp.json()
            .then((response_json) => {
                console.log("resp_json ==", response_json);
                var to_send = {
                    "player_id": parsedLine.first_player_id,
                    "match_id": response_json.match_id,
                    "score": parsedLine.first_player_score,
                    "is_blue": true
                }
                const responseCreateMatchLinkFirst = fetch('http://localhost:8089/api/match_user', {
                    method: 'POST',
                    headers: {
                        'Accept': 'application/json',
                        'Content-Type': 'application/json',
                      },
                      body: JSON.stringify(
                        to_send
                      )
                });
                responseCreateMatchLinkFirst.then((resp) => {
                    var to_send_second = {
                        "player_id": parsedLine.second_player_id,
                        "match_id": response_json.match_id,
                        "score": parsedLine.second_player_score,
                        "is_blue": false
                    }
                    const responseCreateMatchLinkSecond = fetch('http://localhost:8089/api/match_user', {
                        method: 'POST',
                        headers: {
                            'Accept': 'application/json',
                            'Content-Type': 'application/json',
                          },
                          body: JSON.stringify(
                            to_send_second
                          )
                    });
                    responseCreateMatchLinkSecond.then((resp) =>
                    {
                        console.log("ALL GREAT!!")
                        let lastRes = document.getElementById("lastRes");
                        if (lastRes != null) {
                            lastRes.innerHTML = "Отправил в базу данных матч с id=" + parsedLine.match_osu_id;
                        }
                        
                    })
                })
            })
            .then((test) => {
                console.log(test);
            })
            .catch()
        })
        response.then((resp) => {
            
            
        })
        .catch((err) => {
            console.log("error happended", err);
        })
    };

    const handleParseClick = async () => {
        setParsedLines([]);
        let textarea_value = (document.getElementById("ParseLinks") as HTMLInputElement).value;
        const mplinks: { mplink: string; warmups: number; skip_last: number; }[] = [];
        if (textarea_value.length < 1) {
            return;
        }
        let spltted_mplinks = textarea_value.split("\n");
        spltted_mplinks.forEach(function(line: string) {
            let splitted_line = line.split(',');
            let mplink = splitted_line[0];
            if (mplink.length < 3) {
                return
            }
            let warmups = 0;
            let skip_last = 0;
            if (splitted_line.length > 1) {
                warmups = parseInt(splitted_line[1]);
            }
            if (splitted_line.length > 2) {
                skip_last = parseInt(splitted_line[2]);
            }
            if (isNaN(warmups)) {
                warmups = 0;
            }
            if (isNaN(skip_last))
            {
                skip_last = 0;
            }
            mplinks.push({"mplink": mplink, "warmups": warmups, "skip_last": skip_last});
        });
    
        const response = await fetch('http://localhost:8089/api/parse_scrims', {
            method: 'POST',
            headers: {
              'Accept': 'application/json',
              'Content-Type': 'application/json',
            },
            body: JSON.stringify(
                mplinks,
            )
          })
        const parse_result = await response.json();
        const parsed_lines = parse_result["parsed_lines"];
        let string_to_show = "";
        let result = document.getElementById("result");
        if (result === null) return;
        result.innerHTML = "";
        setParsedLines(parsed_lines);
        console.log(parsedLines);

    }

    const handleFirstPlayerScore =(value: string, line: ParsedLine) => {
        console.log("changed first score player line")
        line.first_player_score = parseInt(value);
        setParsedLines(parsedLines);
        console.log(parsedLines);
        console.log(line);
    }
    const handleSecondPlayerScore =(value: string, line: ParsedLine) => {
        line.second_player_score = parseInt(value);
        setParsedLines(parsedLines);
    }

    let firstPlayerWon = "_first_player_won";
    let secondPlayerWon = "_second_player_won";
    return (<div><h1>Здесь вы можете отправить матчи на проверку:</h1>
    Синтаксис отправки (через запятую): ссылка,количество разминочных карт,количество карт с конца которые нужно пропустить
    Пример:https://osu.ppy.sh/community/matches/111534249/,2,3
    <br></br>
    <textarea id="ParseLinks" style={{width: "500px", height:"500px"}}></textarea>
    <button onClick={handleParseClick}>SUBMIT</button>
    <p id="lastRes">
    </p>
    <p id="result" style={{display: "none"}}>
    </p>  {/* key={secondPlayerWon + line.second_player_score} */ }
        <div className="grid grid-cols-4 gap-4 p-4">
            {parsedLines.map((line: ParsedLine) => (
                <div key={line.id} className="flex items-center justify-between p-4 bg-white shadow rounded-lg">
                    <b>{line.first_player_username}
                    <input id={line.id + firstPlayerWon} type="number" min="0" max="50" defaultValue={line.first_player_score} 
                    onChange={e => handleFirstPlayerScore(e.target.value, line)}/></b>
                    -
                    <input id={line.id + secondPlayerWon} type="number" min="0" max="50" defaultValue={line.second_player_score}
                     onChange={e => handleSecondPlayerScore(e.target.value, line)}/>  
                    {line.second_player_username}
                    <button className="btn btn-outline-primary" onClick={() => SendToDB(line)}>SEND TO DATABASE</button>
                </div>
            ))}
        </div>
    </div>
    );
}