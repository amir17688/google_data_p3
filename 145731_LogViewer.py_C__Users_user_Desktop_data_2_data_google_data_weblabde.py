"""Subclass of LogViewerBase, which is generated by wxFormBuilder."""

import wx
import mst_gui

import LogEntry

# Implementing LogViewerBase
class LogViewer( mst_gui.LogViewerBase ):
	
	def __init__( self, parent, log_entry ):
		mst_gui.LogViewerBase.__init__( self, parent )
		self.mLogEntry = log_entry
		self.mTimeNumText.SetValue("%s [%s]" % (log_entry.Time, str(log_entry.Num)))
		self.mSentText.SetValue(log_entry.Sent)
		self.mReceivedText.SetValue(log_entry.Received)
		
	def OnClose(self, event):
		self.EndModal(0)
		
	def OnCloseClicked(self, event):
		self.EndModal(0)