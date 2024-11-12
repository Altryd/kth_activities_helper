package match

import (
	"github.com/go-chi/chi/v5/middleware"
	"github.com/go-chi/render"
	resp "kth_activities_helper/internal/lib/response"
	"kth_activities_helper/internal/models"
	"log/slog"
	"net/http"
)

type ParseResponse struct {
	resp.Response
	Matches []models.Matches `json:"matches,omitempty"`
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
		// var req []Line
		// var test map[string]interface{}
		// r.Body.Close()
		// body, err := io.ReadAll(r.Body)
		// err = json.Unmarshal(body, &test)
		// panic(err)
		var req []Line
		err := render.DecodeJSON(r.Body, &req)

		if err != nil {
			panic(err)
			localLog.Error("Failed to decode request body")
			render.JSON(w, r, resp.BadRequest("Failed to decode request"))
			return
		}
		//print(req)
		/*
			matches, err := matchesParser.ParseMatches()
			if err != nil {
				localLog.Error("Failed to select all matches", slog.String("error", err.Error()))
				render.JSON(w, r, resp.Error("Failed to select all matches"))
			}

			localLog.Info("Selected all matches")

			render.JSON(w, r, GetAllResponse{
				Response: resp.OK(),
				Matches:  matches,
			})
		*/
		return
	}
}
