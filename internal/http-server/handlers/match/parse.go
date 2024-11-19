package match

import (
	"github.com/Altryd/osuParseMpLinks"
	"github.com/go-chi/chi/v5/middleware"
	"github.com/go-chi/render"
	resp "kth_activities_helper/internal/lib/response"
	"kth_activities_helper/internal/models"
	"log/slog"
	"net/http"
	"time"
)

type ParseResponse struct {
	resp.Response
	ParsedLines []ParsedLine `json:"parsed_lines,omitempty"`
}

type ParsedLine struct {
	Id                   uint64    `json:"id"`
	MatchOsuID           uint64    `json:"match_osu_id"`
	MatchTypeId          uint64    `json:"match_type_id"`
	Date                 time.Time `json:"date"`
	FirstPlayerId        uint64    `json:"first_player_id"`
	FirstPlayerUsername  string    `json:"first_player_username"`
	FirstPlayerScore     uint64    `json:"first_player_score"`
	SecondPlayerId       uint64    `json:"second_player_id"`
	SecondPlayerUsername string    `json:"second_player_username"`
	SecondPlayerScore    uint64    `json:"second_player_score"`
}

type Line struct {
	Mplink   string `json:"mplink"`
	Warmups  int    `json:"warmups"`
	SkipLast int    `json:"skip_last"`
}
type ParseRequest struct {
	MpLinks string `json:"mplinks"`
	Lines   []Line
}

type MatchesParser interface {
	ParseMatches([]Line) ([]models.Matches, error)
}

func ParseMatches(log *slog.Logger) http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		const op = "handlers.match.parse.ParseMatches"
		localLog := log.With(
			slog.String("op", op),
			slog.String("request_id", middleware.GetReqID(r.Context())),
		)

		var req []Line
		err := render.DecodeJSON(r.Body, &req)

		if err != nil {
			localLog.Error("Failed to decode request body")
			w.WriteHeader(http.StatusBadRequest)
			render.JSON(w, r, resp.BadRequest("Failed to decode request"))
			return
		}
		secretData, err := osuParseMpLinks.NewSecretData("internal/config/secrets.json")
		if err != nil {
			localLog.Error("Failed to get secret data")
			w.WriteHeader(http.StatusInternalServerError)
			render.JSON(w, r, resp.Error("Failed to get to API"))
			return
		}
		client := osuParseMpLinks.HttpClient{SecretDataConfig: secretData,
			AccessToken: "",
			Client:      &http.Client{}}
		client.UpdateToken("internal/config/secrets.json")
		var result []ParsedLine
		for number, line := range req {
			parsingConfig := osuParseMpLinks.ParsingConfig{Warmups: line.Warmups, SkipLast: line.SkipLast,
				Verbose: false, Debug: false}
			_, userDictForOutput, additionalInfo, err := client.ParseScrim(line.Mplink, parsingConfig)
			if err != nil {
				localLog.Error("Failed to parse scrim")
				w.WriteHeader(http.StatusInternalServerError)
				render.JSON(w, r, resp.Error("Failed to parse scrim"))
				return
			}
			matchID := uint64(additionalInfo["id"].(float64))
			date, _ := time.Parse("2006-01-02T15:04:05+00:00", additionalInfo["start_time"].(string))
			parsedLine := ParsedLine{Id: uint64(number), MatchOsuID: matchID, MatchTypeId: 1, Date: date, // TODO изменить потом нормально matchtype
				FirstPlayerId: userDictForOutput[0].OsuId, FirstPlayerUsername: userDictForOutput[0].Username,
				FirstPlayerScore: userDictForOutput[0].MapsWon,
				SecondPlayerId:   userDictForOutput[1].OsuId, SecondPlayerUsername: userDictForOutput[1].Username,
				SecondPlayerScore: userDictForOutput[1].MapsWon}
			result = append(result, parsedLine)
			// print(allScoresList, userDictForOutput)
		}
		render.JSON(w, r, ParseResponse{
			Response:    resp.OK(),
			ParsedLines: result,
		})
		return
	}
}
