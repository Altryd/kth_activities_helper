'use client'
type ParsedLine = {
    id: number,
    match_osu_id: number,
    match_type_id: number,
    date: Date,
    first_player_id: number,
    first_player_username: string,
    first_player_score: number,
    second_player_id: number,
    second_player_username: string,
    second_player_score: number
};

export default  function ParseScrims() {
    const handleParseClick = async () => {
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
        
        // console.log(mplinks);
        const response = await fetch('http://localhost:8090/api/parse_scrims', {
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
        parsed_lines.map((parsedLine: ParsedLine) => (
            console.log(parsedLine)
        ))
        console.log("GOTP ARSING !!");

    }
    return <div><h1>Здесь вы можете отправить матчи на проверку:</h1>
    Синтаксис отправки (через запятую): ссылка,количество разминочных карт,количество карт с конца которые нужно пропустить
    Пример:https://osu.ppy.sh/community/matches/111534249/,2,3
    <br></br>
    <textarea id="ParseLinks" style={{width: "500px", height:"500px"}}></textarea>
    <button onClick={handleParseClick}>SUBMIT</button>
    </div>;
}