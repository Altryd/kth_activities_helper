package utility

import (
	"encoding/json"
	"errors"
	"fmt"
	"io"
	"kth_activities_helper/internal/database"
	"kth_activities_helper/internal/models"
	"log/slog"
	"os"
)

func UploadPlayers(pathToJson string, storage *database.Storage, log *slog.Logger) error {
	userList, err := storage.SelectUsers()
	if err != nil {
		return err
	}
	if len(userList) > 0 {
		log.Info("users are already existing in database")
		return errors.New("users are already existing in database")
	}
	jsonFile, err := os.Open(pathToJson)
	if err != nil {
		return err
	}
	defer jsonFile.Close()

	byteValue, _ := io.ReadAll(jsonFile)
	var userDataList []models.User
	err = json.Unmarshal(byteValue, &userDataList)
	if err != nil {
		return err
	}
	// fmt.Print(userDataList)
	for _, userData := range userDataList {
		osuId, err := storage.CreateUser(userData.OsuId, userData.DiscordId, userData.Rating,
			userData.Username, userData.Active, userData.RoleId)
		// fmt.Println(osuId, err)
		if err != nil {
			log.Error(fmt.Sprintf("Failed to create user with id=%d", userData.OsuId))
		} else {
			log.Info(fmt.Sprintf("Created user with id=%d", osuId))
		}
	}
	return nil
}

func UploadMatches(pathToJson string, storage *database.Storage, log *slog.Logger) error {
	matchList, err := storage.SelectMatches()
	if err != nil {
		return err
	}
	if len(matchList) > 0 {
		log.Info("matches are already existing in database")
		return errors.New("matches are already existing in database")
	}
	jsonFile, err := os.Open(pathToJson)
	if err != nil {
		return err
	}
	defer jsonFile.Close()

	byteValue, _ := io.ReadAll(jsonFile)
	var matchDataList []models.Matches
	err = json.Unmarshal(byteValue, &matchDataList)
	if err != nil {
		return err
	}
	// fmt.Print(matchDataList)
	for _, matchData := range matchDataList {
		matchId, err := storage.CreateMatch(matchData.MatchOsuID, matchData.MatchTypeId, matchData.Date)
		// fmt.Println(osuId, err)
		if err != nil {
			log.Error(fmt.Sprintf("Error adding match to database with id: %s", matchData.Id))
		} else {
			log.Info(fmt.Sprintf("Match added to database, id=%d ", matchId))
		}
	}
	return nil
}

func UploadMatchUserScrims(pathToJson string, storage *database.Storage, log *slog.Logger) error {
	matchUserScrims, err := storage.SelectMatchUserScrims()
	if err != nil {
		return err
	}
	if len(matchUserScrims) > 0 {
		log.Info("matchUserScrims are already existing in database")
		return errors.New("matchUserScrims are already existing in database")
	}
	jsonFile, err := os.Open(pathToJson)
	if err != nil {
		return err
	}
	defer jsonFile.Close()

	byteValue, _ := io.ReadAll(jsonFile)
	var matchUserScrimDataList []models.MatchUserScrim
	err = json.Unmarshal(byteValue, &matchUserScrimDataList)
	if err != nil {
		return err
	}
	for _, matchUserScrimData := range matchUserScrimDataList {
		_, _, err := storage.CreateMatchUserScrim(matchUserScrimData.PlayerId, matchUserScrimData.MatchId,
			matchUserScrimData.Score, matchUserScrimData.IsBlue, matchUserScrimData.RatingChange)
		if err != nil {
			log.Error(err.Error())
		}
	}
	return nil
}
