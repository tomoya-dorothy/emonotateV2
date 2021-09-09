import React, { useEffect } from 'react';
import { Badge } from '@material-ui/core';
import ListItem from '@material-ui/core/ListItem';
import ListItemIcon from '@material-ui/core/ListItemIcon';
import ListItemText from '@material-ui/core/ListItemText';
import HomeIcon from '@material-ui/icons/Home';
import HistoryIcon from '@material-ui/icons/History';
import MovieIcon from '@material-ui/icons/Movie';
import TextFormatIcon from '@material-ui/icons/TextFormat';
import MailIcon from '@material-ui/icons/Mail';

export const mainListItems = (numRequest) => {
  return (
    <div>
      <ListItem button component="a" href="/app/dashboard/">
        <ListItemIcon>
          <HomeIcon />
        </ListItemIcon>
        <ListItemText primary="ホーム" />
      </ListItem>
      <ListItem button component="a" href="/app/history/">
        <ListItemIcon>
          <HistoryIcon />
        </ListItemIcon>
        <ListItemText primary="履歴" />
      </ListItem>
      <ListItem button component="a" href="/app/content/">
        <ListItemIcon>
          <MovieIcon />
        </ListItemIcon>
        <ListItemText primary="コンテンツ" />
      </ListItem>
      <ListItem button component="a" href="/app/word/">
        <ListItemIcon>
          <TextFormatIcon />
        </ListItemIcon>
        <ListItemText primary="表現語" />
      </ListItem>
      <ListItem button component="a" href="/app/requests/">
        <ListItemIcon>
        <Badge badgeContent={numRequest} color="primary">
          <MailIcon />
        </Badge>
        </ListItemIcon>
        <ListItemText primary="依頼" />
      </ListItem>
    </div>
  );
};
