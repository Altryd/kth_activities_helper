package user

import (
	"fmt"
	"kth_activities_helper/internal/database"
	resp "kth_activities_helper/internal/lib/response"
	"kth_activities_helper/internal/security"
	"log/slog"
	"net/http"

	"github.com/go-chi/chi/v5/middleware"
	"github.com/go-chi/render"
)

type SubscribeResponse struct {
	resp.Response
}

func Subscribe(log *slog.Logger, storage *database.Storage) http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		const op = "handlers.user.Subscribe"
		localLog := log.With(
			slog.String("op", op),
			slog.String("request_id", middleware.GetReqID(r.Context())),
		)

		props, ok := r.Context().Value("props").(*security.Claims)
		if !ok {
			localLog.Error("Failed to do discordOauth because of context")
			render.JSON(w, r, resp.Error("Failed to do discord OAuth"))
			return
		}
		localLog.Info("props: ", props.OsuUserID, props.DiscordUserId)

		discordID := props.DiscordUserId
		fmt.Println(discordID)
		render.JSON(w, r, SubscribeResponse{
			Response: resp.OK(),
		})
		return
	}
}
