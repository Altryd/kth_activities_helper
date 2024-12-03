package user

import (
	"encoding/json"
	"github.com/Altryd/osuParseMpLinks"
	"github.com/go-chi/chi/v5/middleware"
	"github.com/go-chi/render"
	"io"
	resp "kth_activities_helper/internal/lib/response"
	"kth_activities_helper/internal/models"
	"kth_activities_helper/internal/security"
	"log/slog"
	"net/http"
	url2 "net/url"
	"strconv"
	"strings"
	"time"
)

type OsuOAuthResponse struct {
	resp.Response
	Username string `json:"username"`
	OsuId    uint64 `json:"osu_id"`
}

type UserSelectorCreator interface {
	SelectOneUser(osuId uint64) (models.User, error)
	CreateUser(osuId uint64, discordId uint64, rating uint32, username string, active bool) (uint64, error)
}

func GetOsuCode(log *slog.Logger, oneUserSelector UserSelectorCreator) http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		const op = "handlers.user.get.GetOne"
		localLog := log.With(
			slog.String("op", op),
			slog.String("request_id", middleware.GetReqID(r.Context())),
		)
		// PART 0: GETTING CODE
		var queryResults = r.URL.Query() // TODO : можно подумать над state, но как бы неважно пока что
		if len(queryResults) != 2 {
			http.Error(w, http.StatusText(400), 400) // TODO: redirect here
			return
		}
		var code = queryResults.Get("code")
		localLog.Info("Got code", slog.String("code", code))

		// PART 1: getting token

		var apiUrl = "https://osu.ppy.sh"
		var resource = "/oauth/token"
		data := url2.Values{}
		secretData, err := osuParseMpLinks.NewSecretData("internal/config/secrets.json")
		if err != nil {
			localLog.Error("Failed to get secret data")
			w.WriteHeader(http.StatusInternalServerError)
			http.Error(w, http.StatusText(500), 500)
			return
		}
		data.Set("client_id", strconv.Itoa(secretData.ClientId))
		data.Set("client_secret", secretData.ClientSecret)
		data.Set("grant_type", "authorization_code")
		data.Set("code", code)
		data.Set("redirect_uri", "http://localhost:8089/api/oauth/osu")

		u, _ := url2.ParseRequestURI(apiUrl)
		u.Path = resource
		urlStr := u.String()
		client := &http.Client{}
		req, err := http.NewRequest(http.MethodPost, urlStr, strings.NewReader(data.Encode()))
		if err != nil {
			localLog.Error("Something bad happened with post request")
			return
		}
		req.Header.Add("Content-Type", "application/x-www-form-urlencoded")
		req.Header.Add("Accept", "application/json")
		response, err := client.Do(req)
		if err != nil {
			localLog.Error("Something bad happened with post request")
			http.Error(w, http.StatusText(500), 500)
			return
		}
		defer response.Body.Close()
		body, err := io.ReadAll(response.Body)
		var dataRead map[string]interface{}
		err = json.Unmarshal(body, &dataRead)
		if err != nil {
			return
		}
		if response.StatusCode != 200 {
			localLog.Error("Something bad when accessing ", slog.String(urlStr, "url"))
			http.Error(w, http.StatusText(500), 500)
			return
		}

		// PART2: GOT ACCESS TOKEN DISCORD, getting user info

		accessToken := dataRead["access_token"].(string)
		apiUrl = "https://osu.ppy.sh"
		resource = "api/v2/me/osu"

		u, _ = url2.ParseRequestURI(apiUrl)
		u.Path = resource
		urlStr = u.String()
		req, _ = http.NewRequest(http.MethodGet, urlStr, nil)
		req.Header.Add("Authorization", "Bearer"+" "+accessToken)
		req.Header.Add("Accept", "application/json")
		response, err = client.Do(req)
		if err != nil {
			localLog.Error("Something bad happened with GET request")
			http.Error(w, http.StatusText(500), 500)
			return
		}
		defer response.Body.Close()
		body, _ = io.ReadAll(response.Body)
		err = json.Unmarshal(body, &dataRead)
		if err != nil {
			http.Error(w, http.StatusText(500), 500)
			return
		}
		if response.StatusCode != 200 {
			localLog.Error("Something bad when accessing ", slog.String(urlStr, "url"))
			http.Error(w, http.StatusText(500), 500)
			return
		}
		id := uint64(dataRead["id"].(float64))
		username := dataRead["username"].(string)

		var idInDatabase uint64 = 0
		user, err := oneUserSelector.SelectOneUser(id)
		if err != nil {
			id_, err := oneUserSelector.CreateUser(id, 0, 0, username, false)
			if err != nil {
				localLog.Error("Failed to create user", slog.String("error", err.Error()))
				render.JSON(w, r, resp.Error("Failed to create match"))
				return
			}
			idInDatabase = id_
			user, _ = oneUserSelector.SelectOneUser(idInDatabase) // not checking error because we just added the user to database
		} else {
			idInDatabase = user.OsuId
		}
		// http.SetCookie(w, &http.Cookie{Name: username, HttpOnly: false})

		accessTokenOurDb, err := security.GenerateToken(&user, "access")
		if err != nil {
			localLog.Error("Failed to generate access token")
			render.JSON(w, r, resp.Error("Failed to generate access token"))
			return
		}
		security.SetCookie(w, "jwt", accessTokenOurDb, time.Now().Add(time.Hour*2))
		render.JSON(w, r, OsuOAuthResponse{ // TODO: redirect here
			Response: resp.OK(),
			OsuId:    id,
			Username: username,
		})
		return
	}
}
