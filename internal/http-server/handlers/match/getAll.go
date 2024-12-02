package match

import (
	"github.com/go-chi/chi/v5/middleware"
	"github.com/go-chi/render"
	resp "kth_activities_helper/internal/lib/response"
	"kth_activities_helper/internal/models"
	"log/slog"
	"net/http"
	"time"
)

type player_struct struct {
	OsuId     uint64
	DiscordId uint64
	Rating    uint32
	Username  string
	Active    bool
}

type scrim_struct struct {
	PlayerId     uint64
	Player       player_struct
	Score        uint64
	IsBlue       bool
	RatingChange float64
}

type match_struct struct {
	Id             uint64
	MatchOsuID     uint64
	MatchTypeId    uint64
	Date           time.Time
	MatchUserScrim []scrim_struct
	IsApproved     bool
}

type GetAllResponse struct {
	resp.Response
	Matches []match_struct `json:"matches,omitempty"`
}

type MatchesSelector interface {
	SelectMatches() ([]models.Matches, error)
}

func GetAll(log *slog.Logger, matchesSelector MatchesSelector) http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		const op = "handlers.match.get.GetAll"
		localLog := log.With(
			slog.String("op", op),
			slog.String("request_id", middleware.GetReqID(r.Context())),
		)

		matches, err := matchesSelector.SelectMatches()
		if err != nil {
			localLog.Error("Failed to select all matches", slog.String("error", err.Error()))
			render.JSON(w, r, resp.Error("Failed to select all matches"))
			return
		}
		localLog.Info("Selected all matches")

		var match_response []match_struct

		for _, match := range matches {
			var scrims []scrim_struct
			for _, scrim := range match.MatchUserScrim {
				scrims = append(scrims,
					scrim_struct{
						PlayerId: scrim.PlayerId,
						Player: player_struct{
							OsuId:     scrim.Player.OsuId,
							DiscordId: scrim.Player.DiscordId,
							Rating:    scrim.Player.Rating,
							Username:  scrim.Player.Username,
							Active:    scrim.Player.Active,
						},
						Score:        scrim.Score,
						IsBlue:       scrim.IsBlue,
						RatingChange: scrim.RatingChange,
					})
			}
			match_response = append(match_response, match_struct{
				Id:             match.Id,
				MatchOsuID:     match.MatchOsuID,
				MatchTypeId:    match.MatchTypeId,
				Date:           match.Date,
				MatchUserScrim: scrims,
				IsApproved:     match.IsApproved,
			})
		}

		render.JSON(w, r, GetAllResponse{
			Response: resp.OK(),
			Matches:  match_response,
		})
		return
	}
}
