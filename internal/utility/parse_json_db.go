package utility

import (
	"encoding/json"
	"errors"
	"fmt"
	"io"
	"kth_activities_helper/internal/database"
	"kth_activities_helper/internal/models"
	"os"
)

func UploadPlayers(pathToJson string, storage *database.Storage) error {
	jsonFile, err := os.Open(pathToJson)
	if err != nil {
		return err
	}
	defer jsonFile.Close()
	userList, err := storage.SelectUsers()
	if err != nil {
		return err
	}
	if len(userList) > 0 {
		return errors.New("users are already existing in database")
	}

	byteValue, _ := io.ReadAll(jsonFile)
	var userDataList []models.User
	err = json.Unmarshal(byteValue, &userDataList)
	if err != nil {
		return err
	}
	// fmt.Print(userDataList)
	for _, userData := range userDataList {
		osuId, err := storage.CreateUser(userData.OsuId, userData.DiscordId, userData.Rating,
			userData.Username, userData.Active)
		fmt.Println(osuId, err)
	}
	return nil
}

func UploadMatches(pathToJson string, storage *database.Storage) error {
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
		osuId, err := storage.CreateMatch(matchData.Id, matchData.MatchTypeId, matchData.Date)
		fmt.Println(osuId, err)
	}
	return nil
}
